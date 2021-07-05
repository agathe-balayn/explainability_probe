from django.test import TestCase
from SECAAlgo.query import query_classes, query_rules, universal_query
from SECAAlgo.models import Images, Annotations, Sessions
from unittest.mock import patch


def mock_pipeline(image_set_setting, binary_task_classes,
                  max_antecedent_length, min_support_score,
                  min_lift_score, min_confidence_score,
                  filter_concepts, or_queries,
                  desired_classes, or_exclude,
                  or_not_query, exclude_concepts,
                  class_selection, predicted_class,
                  not_predicted_class,
                  exclude_predicted_classes,
                  exclude_true_classes,
                  only_true_class,
                  only_predicted_class, session_id):
    checkobject = {}
    checkobject['image_set_setting'] = image_set_setting
    # checkobject['return_setting'] = return_setting
    checkobject['binary_task_classes'] = binary_task_classes
    checkobject['max_antecedent_length'] = max_antecedent_length
    checkobject['min_support_score'] = min_support_score
    checkobject['min_lift_score'] = min_lift_score
    checkobject['min_confidence_score'] = min_confidence_score
    checkobject['filter_concepts'] = filter_concepts
    checkobject['or_queries'] = or_queries
    checkobject['desired_classes'] = desired_classes
    checkobject['or_exclude'] = or_exclude
    checkobject['exclude_concepts'] = exclude_concepts
    checkobject['or_not_query'] = or_not_query
    checkobject['class_selection'] = class_selection
    checkobject['predicted_class'] = predicted_class
    checkobject['not_predicted_class'] = not_predicted_class
    checkobject['exclude_predicted_classes'] = exclude_predicted_classes
    checkobject['exclude_true_classes'] = exclude_true_classes
    checkobject['only_true_class'] = only_true_class
    checkobject['only_predicted_class'] = only_predicted_class
    checkobject['session_id'] = session_id
    return checkobject, "supp_conf", 200


class pipeline_setup(TestCase):
    def setUp(self):
        # setting up objects in the database
        image1 = Images(image_name="image 1", actual_image="This is definitely a real image",
                        predicted_image="Not the correct image")
        image2 = Images(image_name="image 2",
                        actual_image="B-2 spirit stealth bomber", predicted_image="tree")
        image3 = Images(image_name="image 3",
                        actual_image="table", predicted_image="table")
        image1.save()
        image2.save()
        image3.save()

        predictionSet = Sessions()
        predictionSet.save()
        predictionSet.images.add(image1)
        predictionSet.images.add(image2)
        predictionSet.images.add(image3)

        image1_annotation1 = Annotations(image=image1, annotation="real", bounding_box_coordinates="[20, 0, 69, 1]",
                                         weight=4, reason="because its definitely real")
        image1_annotation2 = Annotations(image=image1, annotation="leg", bounding_box_coordinates="[1, 1, 2, 2]",
                                         weight=1, reason="it is a leg")
        image2_annotation1 = Annotations(image=image2, annotation="wing", bounding_box_coordinates="[0, 0, 2, 5]",
                                         weight=6, reason="these are wings")
        image2_annotation2 = Annotations(image=image2, annotation="bombing_doors",
                                         bounding_box_coordinates="[2, 0, 3, 4]", weight=9,
                                         reason="these are literally bombing doors")
        image2_annotation3 = Annotations(image=image2, annotation="real", bounding_box_coordinates="[5, 2, 10, 4]",
                                         weight=3, reason="its real")
        image3_annotation1 = Annotations(image=image3, annotation="leg", bounding_box_coordinates="[2, 3, 10, 10]",
                                         weight=10, reason="this is a table leg")

        image1_annotation1.save()
        image1_annotation2.save()

        image2_annotation1.save()
        image2_annotation2.save()
        image2_annotation3.save()

        image3_annotation1.save()

    def tearDown(self) -> None:
        return super().tearDown()


class SimpleRuleQueryTests(TestCase):
    @patch("SECAAlgo.query.execute_rule_mining_pipeline", mock_pipeline)
    # @patch("SECAAlgo.query.query_rules")
    def test_query_all_defaults(self):
        query = {
            "session_id": 1
        }

        res, status = query_rules(query)

        self.assertEquals(res['image_set_setting'], "BINARY_MATRIX_VIEW")
        self.assertEquals(res['binary_task_classes'], [])
        self.assertEquals(res['max_antecedent_length'], 3)
        self.assertEquals(res['min_support_score'], 0.000001)
        self.assertEquals(res['min_lift_score'], 0.2)
        self.assertEquals(res['min_confidence_score'], 0.3)
        self.assertEquals(res['filter_concepts'], "ALL")
        self.assertEquals(res['or_queries'], [])
        self.assertEquals(res['desired_classes'], ["ALL"])
        self.assertEquals(res['or_exclude'], [])
        self.assertEquals(res['exclude_concepts'], [])
        self.assertEquals(status, 200)

    @patch("SECAAlgo.query.execute_rule_mining_pipeline", mock_pipeline)
    def test_query_setting_all(self):
        query = {
            "image_setting": "all",
            "session_id": 1
        }

        res, status = query_rules(query)
        self.assertEquals(res['image_set_setting'], "ALL_IMAGES")

    @patch("SECAAlgo.query.execute_rule_mining_pipeline", mock_pipeline)
    def test_query_setting_correct_only(self):
        query = {
            "image_setting": "correct_only",
            "session_id": 1
        }

        res, status = query_rules(query)
        self.assertEquals(res['image_set_setting'], "CORRECT_PREDICTION_ONLY")

    @patch("SECAAlgo.query.execute_rule_mining_pipeline", mock_pipeline)
    def test_query_setting_incorrect_only(self):
        query = {
            "image_setting": "incorrect_only",
            "session_id": 1
        }

        res, status = query_rules(query)
        self.assertEquals(res['image_set_setting'],
                          "WRONG_PREDICTION_ONLY")

    @patch("SECAAlgo.query.execute_rule_mining_pipeline", mock_pipeline)
    def test_query_exclude_one(self):
        exclude_list = ["thing_to_exclude_1", "Another_one", "another_another_one"]

        query = {
            "exclude": exclude_list,
            "session_id": 1
        }

        res, status = query_rules(query)
        self.assertEquals(res['exclude_concepts'], exclude_list)

    @patch("SECAAlgo.query.execute_rule_mining_pipeline", mock_pipeline)
    def test_query_exclude_two(self):
        exclude_list_1 = ["thing_to_exclude_1",
                          "Another_one", "another_another_one", "one AND two"]
        exclude_list_2 = ["thing_to_exclude_2",
                          "This_isnt_two", "two AND three"]
        exclude_frozenset = [frozenset({"thing_to_exclude_2"}), frozenset(
            {"This_isnt_two"}), frozenset({"two", "three"})]

        query = {
            "exclude": exclude_list_1,
            "exclude": exclude_list_2,
            "session_id": 1
        }

        res, status = query_rules(query)
        self.assertEquals(status, 200)
        self.assertEquals(res['exclude_concepts'], exclude_frozenset)

    @patch("SECAAlgo.query.execute_rule_mining_pipeline", mock_pipeline)
    def test_query_exclude_one(self):
        or_exclude_list = ["thing_to_exclude_1",
                           "Another_one", "two AND three"]
        or_exclude_frozenset = [frozenset({"thing_to_exclude_1"}), frozenset({"Another_one"}),
                                frozenset({"two", "three"})]

        query = {
            "or_exclude": or_exclude_list,
            "session_id": 1
        }

        res, status = query_rules(query)
        self.assertEquals(res['or_exclude'], or_exclude_frozenset)

    @patch("SECAAlgo.query.execute_rule_mining_pipeline", mock_pipeline)
    def test_query_includes(self):
        include_list = ["thing_to_include_1", "Another_one", "three AND five"]
        or_include_list = ["or_include_list"]
        include_frozenset = [frozenset({"thing_to_include_1"}), frozenset({"Another_one"}),
                             frozenset({"three", "five"})]
        or_include_frozenset = [frozenset({"or_include_list"})]

        query = {
            "include": include_list,
            "or_query": or_include_list,
            "session_id": 1
        }

        res, status = query_rules(query)
        self.assertEquals(res['filter_concepts'], include_frozenset)
        self.assertEquals(res['or_queries'], or_include_frozenset)

    @patch("SECAAlgo.query.execute_rule_mining_pipeline", mock_pipeline)
    def test_query_exclude_one(self):
        add_class_list = ["class1", "class2"]
        desired_true_classes = ["tables", "stealth_bombers"]

        query = {
            "image_setting": "binary_matrix",
            "add_class": add_class_list,
            "true_class": desired_true_classes,
            "session_id": 1
        }

        res, status = query_rules(query)
        self.assertEquals(res['image_set_setting'], "BINARY_MATRIX_VIEW")
        self.assertEquals(res['binary_task_classes'], add_class_list)
        self.assertEquals(res['desired_classes'], desired_true_classes)
        self.assertEquals(status, 200)

    @patch("SECAAlgo.query.execute_rule_mining_pipeline", mock_pipeline)
    def test_query_change_parameters(self):
        query = {
            "max_antecedent_length": 6,
            "min_support_score": 0.69,
            "min_lift_score": 10,
            "min_confidence_score": 42,
            "session_id": 1
        }

        res, status = query_rules(query)
        self.assertEquals(res['max_antecedent_length'], 6)
        self.assertEquals(res['min_support_score'], 0.69)
        self.assertEquals(res['min_lift_score'], 10)
        self.assertEquals(res['min_confidence_score'], 42)
        self.assertEquals(status, 200)

    @patch("SECAAlgo.query.execute_rule_mining_pipeline", mock_pipeline)
    def test_query_filter_rule_and_concept_parameters(self):
        filter_concepts_inputs = ["concept_1", "concept_2"]
        or_query_inputs = ["or_query_1", "or AND query_2"]
        or_exclude_inputs = ["exclude", "these AND inputs"]
        exclude_concepts_inputs = ["separate AND this AND into three"]
        or_not_query_inputs = ["or_not_query", "its AND thing I guess"]
        session_id_input = 23876543

        query = {
            'include': filter_concepts_inputs,
            'or_query': or_query_inputs,
            'or_exclude': or_exclude_inputs,
            'exclude': exclude_concepts_inputs,
            'or_not_query': or_not_query_inputs,
            'session_id': session_id_input
        }

        res, status = query_rules(query)
        self.assertEquals(res['filter_concepts'], [frozenset({'concept_1'}), frozenset({'concept_2'})])
        self.assertEquals(res['or_queries'], [frozenset({'or_query_1'}), frozenset({'or', 'query_2'})])
        self.assertEquals(res['or_exclude'], [frozenset({'exclude'}), frozenset({'these', 'inputs'})])
        self.assertEquals(res['exclude_concepts'], [frozenset({'separate', 'this', 'into three'})])
        self.assertEquals(res['or_not_query'], [frozenset({'or_not_query'}), frozenset({'its', 'thing I guess'})])
        self.assertEquals(res['session_id'], session_id_input)

    @patch("SECAAlgo.query.execute_rule_mining_pipeline", mock_pipeline)
    def test_query_filter_class_parameters(self):
        class_selection_inputs = ["class", "selection" "stuff"]
        predicted_class_inputs = ["predicted", "class", "and all that"]
        not_predicted_class_inputs = ["this", "is", "really", "boring", "to", "do"]
        exclude_predicted_classes_inputs = ["please", "make", "it", "stop"]
        exclude_true_classes_inputs = ["2+2", "=", "4", "-", "1", "that's", "3", "quick", "maths"]
        only_true_class_inputs = ["this is a true input"]
        only_predicted_class_inputs = ["input"]

        query = {
            'class_selection': class_selection_inputs,
            'predicted_class': predicted_class_inputs,
            'not_predicted_class': not_predicted_class_inputs,
            'exclude_predicted_class': exclude_predicted_classes_inputs,
            'exclude_true_class': exclude_true_classes_inputs,
            'only_true_class': only_true_class_inputs,
            'only_predicted_class': only_predicted_class_inputs,
            'session_id': 5
        }

        res, status = query_rules(query)
        self.assertEquals(res['class_selection'], class_selection_inputs)
        self.assertEquals(res['predicted_class'], predicted_class_inputs)
        self.assertEquals(res['not_predicted_class'], not_predicted_class_inputs)
        self.assertEquals(res['exclude_predicted_classes'], exclude_predicted_classes_inputs)
        self.assertEquals(res['exclude_true_classes'], exclude_true_classes_inputs)
        self.assertEquals(res['only_true_class'], only_true_class_inputs)
        self.assertEquals(res['only_predicted_class'], only_predicted_class_inputs)

    def test_query_empty_database(self):
        query = {
            "image_setting": "all",
            "session_id": 1
        }

        res, status = query_rules(query)
        self.assertEquals(
            res, {"There were no results for that combination in the binary matrix"})
        self.assertEquals(status, 206)


class RuleQueryTestsWithDatabase(pipeline_setup):
    def test_query_with_small_database(self):
        query = {
            "image_setting": "all",
            "session_id": 1
        }
        # just making sure the binary matrix does indeed return less than querying for all
        res, status = query_rules(query)
        self.assertEquals(res['rules']['leg'], {'Not the correct image': {'image 1': 'This is definitely a real image',
                                                                          'percent_present': 0.3333333333333333,
                                                                          'percent_correct': 0.0, 'typicality': 1.5},
                                                'table': {'image 3': 'table', 'percent_present': 0.3333333333333333,
                                                          'percent_correct': 1.0, 'typicality': 1.5}})
        self.assertEquals(status, 200)

    def test_query_different_small_database(self):
        query = {
            "image_setting": "binary_matrix",
            "add_class": ["table", "B-2 spirit stealth bomber"],
            "session_id": 1
        }

        res, status = query_rules(query)
        self.assertEquals(res['rules']['leg'], {'table': {'image 3': 'table', 'percent_correct': 1.0,
                                                          'percent_present': 1.0, 'typicality': 1.0}})
        self.assertEquals(status, 200)

    def test_query_with_exclusions(self):
        query = {
            "image_setting": "binary_matrix",
            "add_class": ["table", "B-2 spirit stealth bomber"],
            "include": ["leg"],
            "session_id": 1
        }

        res, status = query_rules(query)
        self.assertEquals(status, 200)
        self.assertEquals(res['rules'], {'leg': {'table': {'image 3': 'table', 'percent_correct': 1.0,
                                                           'percent_present': 1.0, 'typicality': 1.0}}})

    def test_query_include_and_exclude(self):
        query = {
            "image_setting": "binary_matrix",
            "add_class": ["table", "B-2 spirit stealth bomber"],
            "include": ["leg"],
            "exclude": ["leg"],
            "session_id": 1
        }

        res, status = query_rules(query)
        self.assertEquals(status, 200)
        self.assertEquals(res, {'concepts': {}, 'rules': {}})

    def test_query_all_include_and_exclude_is_same_as_all(self):
        query = {
            "image_setting": "all",
            "include": ["leg"],
            "session_id": 1,
        }

        res, status = query_rules(query)
        self.assertEquals(status, 200)
        self.assertEquals(res['rules'], {'leg': {'Not the correct image': {'image 1': 'This is definitely a real image',
                                                                           'percent_present': 0.3333333333333333,
                                                                           'percent_correct': 0.0, 'typicality': 1.5},
                                                 'table': {'image 3': 'table', 'percent_present': 0.3333333333333333,
                                                           'percent_correct': 1.0, 'typicality': 1.5}}})

    def test_query_predicted_classes(self):
        query = {
            "image_setting": "all",
            "predicted_class": ["tree"],
            "session_id": 1
        }

        res, status = query_rules(query)
        self.assertEquals(status, 200)
        self.assertEquals(res['concepts']['real'], {"image 2": "Misclassified",
                                                    "percent_correct": 0.0,
                                                    "percent_present": 0.3333333333333333,
                                                    "typicality": 1.0})

    def test_query_class_selection(self):
        query = {
            "image_setting": "all",
            "class_selection": ["table"],
            "session_id": 1,
        }

        res, status = query_rules(query)
        self.assertEquals(status, 200)
        self.assertEquals(res['concepts'], {'leg': {'image 3': 'Correctly classified',
                                                    'percent_correct': 1.0,
                                                    'percent_present': 0.3333333333333333,
                                                    'typicality': 1.0}})

    def test_query_true_classes(self):
        query = {
            "image_setting": "all",
            "true_class": ["B-2 spirit stealth bomber"],
            "session_id": 1,
        }

        res, status = query_rules(query)

        self.assertEquals(status, 200)
        self.assertEquals(res['concepts']['real'], {'image 2': 'Misclassified', 'percent_present': 0.3333333333333333,
                                                    'percent_correct': 0.0, 'typicality': 1.0})

        self.assertEquals(res['concepts']['wing'], {'image 2': 'Misclassified', 'percent_present': 0.3333333333333333,
                                                    'percent_correct': 0.0, 'typicality': 1.0})
        self.assertEquals(res['concepts']['bombing_doors'], {'image 2': 'Misclassified',
                                                             'percent_present': 0.3333333333333333,
                                                             'percent_correct': 0.0, 'typicality': 1.0})
        # We cannot make tests on the "AND" rules/concepts because the order is random, so sometimes it will be
        # bombing_doors AND real, and other times it will be real AND bombing doors
        # self.assertEquals(res['concepts']['bombing_doors AND real'], {'image 2': 'Misclassified',
        #                                                                'percent_present': 0.3333333333333333,
        #                                                                'percent_correct': 0.0, 'typicality': 1.0})

    def test_query_not_predicted_classes(self):
        query = {
            "image_setting": "all",
            "not_predicted_class": ["tree"],
            "session_id": 1
        }

        res, status = query_rules(query)
        self.assertEquals(status, 200)
        self.assertEquals(res['concepts']['leg'], {'image 1': 'Misclassified',
                                                   'image 3': 'Correctly classified',
                                                   'percent_present': 0.6666666666666666,
                                                   'percent_correct': 0.5, 'typicality': 1.0})

    def test_query_exclude_predicted_classes(self):
        query = {
            "image_setting": "all",
            "predicted_class": ["tree, This is definitely a real image", "table"],
            "exclude_predicted_class": ["tree", "Not the correct image"],
            "session_id": 1
        }

        query2_not_predicted = {
            "image_setting": "all",
            "not_predicted_class": ["tree", "Not the correct image"],
            "session_id": 1
        }

        res, status = query_rules(query)

        not_predicted_res, status2 = query_rules(query2_not_predicted)
        self.assertEquals(res, not_predicted_res)
        self.assertEquals(status, 200)

    def test_query_basic_or_exclusion(self):
        query = {
            "image_setting": "all",
            "session_id": 1,
            "or_exclude": ["real", "leg", "wing"]
        }
        # just making sure the binary matrix does indeed return less than querying for all
        res, status = query_rules(query)
        self.assertEquals(res["concepts"], {'bombing_doors': {
            "image 2": "Misclassified",
            "percent_present": 0.3333333333333333,
            "percent_correct": 0.0,
            "typicality": 1.0
        }})
        self.assertEquals(status, 200)

    def test_query_basic_exclusion(self):
        query = {
            "image_setting": "all",
            "session_id": 1,
            "or_exclude": ["leg", "wing"],
            "exclude": ["real", "real AND bombing_doors"]
        }
        # just making sure the binary matrix does indeed return less than querying for all
        res, status = query_rules(query)
        self.maxDiff = None
        self.assertEquals(status, 200)
        self.assertEquals(res["concepts"], {'bombing_doors': {
            "image 2": "Misclassified",
            "percent_present": 0.3333333333333333,
            "percent_correct": 0.0,
            "typicality": 1.0
        }})

    def test_query_basic_exclusion(self):
        query = {
            "image_setting": "all",
            "session_id": 1,
            "or_exclude": ["leg", "wing"],
            "exclude": ["real", "real AND bombing_doors"]
        }
        # just making sure the binary matrix does indeed return less than querying for all
        res, status = query_rules(query)
        self.assertEquals(status, 200)
        self.assertEquals(res["concepts"], {'bombing_doors': {
            "image 2": "Misclassified",
            "percent_present": 0.3333333333333333,
            "percent_correct": 0.0,
            "typicality": 1.0
        }})

    def test_query_class_selection(self):
        query = {
            "image_setting": "all",
            "session_id": 1,
            "class_selection": ["Not the correct image"]
        }
        # just making sure the binary matrix does indeed return less than querying for all
        res, status = query_rules(query)
        self.assertEquals(status, 200)
        self.maxDiff = None
        self.assertEquals(res["concepts"]['real'], {
            "image 1": "Misclassified",
            "percent_present": 0.3333333333333333,
            "percent_correct": 0.0,
            "typicality": 1.0
        })
        self.assertEquals(res['concepts']['leg'], {
            "image 1": "Misclassified",
            "percent_present": 0.3333333333333333,
            "percent_correct": 0.0,
            "typicality": 1.0
        }
        )

    def test_query_true_class(self):
        query = {
            "image_setting": "all",
            "session_id": 1,
            "true_class": ["tree"]
        }
        # just making sure the binary matrix does indeed return less than querying for all
        res, status = query_rules(query)
        self.assertEquals(status, 200)
        self.assertEquals(res, {"concepts": {}, "rules": {}})

    def test_query_true_class_actually(self):
        query = {
            "image_setting": "all",
            "session_id": 1,
            "true_class": ["table"]
        }
        # just making sure the binary matrix does indeed return less than querying for all
        res, status = query_rules(query)
        self.assertEquals(status, 200)
        self.assertEquals(res['concepts'], {
            "leg": {
                "image 3": "Correctly classified",
                "percent_present": 0.3333333333333333,
                "percent_correct": 1.0,
                "typicality": 1.0
            }
        })


class Class_Query_Test(pipeline_setup):
    def test_images_single(self):
        query = {
            "query": "Images",
            "include": {
                "actual_image": "B-2 spirit stealth bomber"
            }
        }

        res, status = query_classes(query)
        self.assertEquals(res['Response:'], [
            {
                "id": 2,
                "image_name": "image 2",
                "actual_image": "B-2 spirit stealth bomber",
                "predicted_image": "tree"
            }
        ])

    def test_images_no_output(self):
        query = {
            "query": "Images",
            "include": {
                "actual_image": "B-2 spirit stealth bomber",
                "predicted_image": "table"
            }
        }

        res = query_classes(query)
        self.assertEquals(res[0]['Response:'], [])

    def test_annotations_basic_query(self):
        query = {
            "query": "Annotations",
            "include": {
                "weight": 9
            }
        }

        res, status = query_classes(query)

        self.assertEquals(status, 200)
        self.assertEquals(res['Response:'], [
            {
                "image": {
                    "id": 2,
                    "image_name": "image 2",
                    "actual_image": "B-2 spirit stealth bomber",
                    "predicted_image": "tree"
                },
                "annotation": "bombing_doors",
                "bounding_box_coordinates": "[2, 0, 3, 4]",
                "weight": 9,
                "reason": "these are literally bombing doors"
            }
        ])

    def test_annotations_nothing_found(self):
        query = {
            "query": "Annotations",
            "include": {
                "weight": 9,
                "annotation": "real"
            }
        }

        res, status = query_classes(query)

        self.assertEquals(status, 200)
        self.assertEquals(res['Response:'], [])


class UTest_simple_tests(pipeline_setup):
    def test_class_basic(self):
        universal_query_in = {
            "query_type": "class",
            "query": "Images",
            "include": {
                "actual_image": "B-2 spirit stealth bomber"
            }
        }

        class_query = {
            "query": "Images",
            "include": {
                "actual_image": "B-2 spirit stealth bomber"
            }
        }

        uni_res, uni_status = universal_query(universal_query_in)
        class_res, class_status = query_classes(class_query)
        self.assertEquals(uni_status, 200)
        self.assertEquals(class_status, 200)
        self.assertEquals(uni_res, class_res)

    def test_universal_to_rule_query(self):
        universal_query_in = {
            "query_type": "rules",
            "image_setting": "binary_matrix",
            "add_class": ["table", "B-2 spirit stealth bomber"],
            "session_id": 1
        }

        rule_query_in = {
            "image_setting": "binary_matrix",
            "add_class": ["table", "B-2 spirit stealth bomber"],
            "session_id": 1
        }

        uni_res, uni_status = universal_query(universal_query_in)
        rule_res, rule_status = query_rules(rule_query_in)

        self.assertEquals(uni_status, 200)
        self.assertEquals(rule_status, 200)
        self.assertEquals(uni_res, rule_res)
