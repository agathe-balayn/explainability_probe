from unittest.mock import patch
from django.db import transaction
from django.test import TestCase
from SECAAlgo.models import Images, Sessions, Annotations
from SECAAlgo.seca_helper_methods import save_csv_predictions, link_annotations, make_annotations, \
    get_tabular_representation, get_tabular_representation_rule_mining
import json
import pandas
import csv

class TestSaveCSV(TestCase):
    def test_save_csv(self):
        csv_to_string = ""
        with open("SECAAlgo/tests/test_helper_method_files/save_csv_example_file.csv", "r") as csv_file:
            reader = csv.reader(csv_file)
            for next_line in reader:
                if csv_to_string == "":
                    csv_to_string = next_line[0] + "," + next_line[1] + "," + next_line[2]
                else:
                    csv_to_string = csv_to_string + "\n" + next_line[0] + "," + next_line[1] + "," + next_line[2]

        save_csv_predictions({"data_set": csv_to_string, "dataset_name": "set1",
                              "username": []})

        images_in_db = Images.objects.all()
        self.assertEquals(images_in_db.count(), 5)
        self.assertEquals(images_in_db[0].id, 1)
        self.assertEquals(images_in_db[0].image_name, "Image_1")
        self.assertEquals(images_in_db[1].image_name, "Image_2")
        self.assertEquals(images_in_db[2].image_name, "Image_3")
        self.assertEquals(images_in_db[3].image_name, "Image_4")
        self.assertEquals(images_in_db[4].image_name, "Image_5")
        self.assertEquals(images_in_db[0].actual_image, "example_image_test")
        self.assertEquals(images_in_db[0].predicted_image, "different_prediction")
        self.assertEquals(images_in_db[3].actual_image, "B-2 spirit stealth bomber")

        predictions_in_db = Sessions.objects.all()
        self.assertEquals(predictions_in_db.count(), 1)
        self.assertEquals(predictions_in_db[0].id, 1)
        self.assertEquals(predictions_in_db[0].images.all()[0], images_in_db[0])
        self.assertEquals(predictions_in_db[0].images.all()[1], images_in_db[1])
        self.assertEquals(predictions_in_db[0].images.all()[2], images_in_db[2])
        self.assertEquals(predictions_in_db[0].images.all()[3], images_in_db[3])
        self.assertEquals(predictions_in_db[0].images.all()[4], images_in_db[4])
        self.assertEquals(predictions_in_db[0].users.count(), 0)

    def test_save_2_csv_files_different_name(self):
        csv_to_string = ""
        with open("SECAAlgo/tests/test_helper_method_files/save_csv_example_file.csv", "r") as csv_file:
            reader = csv.reader(csv_file)
            for next_line in reader:
                if csv_to_string == "":
                    csv_to_string = next_line[0] + "," + next_line[1] + "," + next_line[2]
                else:
                    csv_to_string = csv_to_string + "\n" + next_line[0] + "," + next_line[1] + "," + next_line[2]

        save_csv_predictions({"data_set": csv_to_string, "dataset_name": "set_1",
                              "username": []})

        save_csv_predictions({"data_set": csv_to_string, "dataset_name": "set_2",
                              "username": []})

        images_in_db = Images.objects.all()
        self.assertEquals(images_in_db.count(), 10)
        self.assertEquals(images_in_db[0].id, 1)
        self.assertEquals(images_in_db[0].image_name, "Image_1")
        self.assertEquals(images_in_db[0].actual_image, "example_image_test")
        self.assertEquals(images_in_db[0].predicted_image, "different_prediction")

        self.assertEquals(images_in_db[5].id, 6)
        self.assertEquals(images_in_db[5].image_name, "Image_1")
        self.assertEquals(images_in_db[5].actual_image, "example_image_test")
        self.assertEquals(images_in_db[5].predicted_image, "different_prediction")
        self.assertEquals(images_in_db[3].actual_image, "B-2 spirit stealth bomber")

        predictions_in_db = Sessions.objects.all()
        self.assertEquals(predictions_in_db.count(), 2)
        self.assertEquals(predictions_in_db[0].id, 1)
        self.assertEquals(predictions_in_db[1].id, 2)
        self.assertEquals(predictions_in_db[0].images.all()[0], images_in_db[0])
        self.assertEquals(predictions_in_db[0].users.count(), 0)

    def test_save_2_csv_files_same_name(self):
        csv_to_string = ""
        with open("SECAAlgo/tests/test_helper_method_files/save_csv_example_file.csv", "r") as csv_file:
            reader = csv.reader(csv_file)
            for next_line in reader:
                if csv_to_string == "":
                    csv_to_string = next_line[0] + "," + next_line[1] + "," + next_line[2]
                else:
                    csv_to_string = csv_to_string + "\n" + next_line[0] + "," + next_line[1] + "," + next_line[2]

        res_string, successful_save, session_id = save_csv_predictions({"data_set": csv_to_string,
                                                                        "dataset_name": "set", "username": []})

        with transaction.atomic():
            fail_string, fail_save, fail_id = save_csv_predictions({"data_set": csv_to_string, "dataset_name": "set",
                                                                    "username": []})
        self.assertEquals(session_id, 1)
        self.assertEquals(fail_id, -1)
        self.assertEquals(successful_save, 200)
        self.assertEquals(fail_save, 417)

        images_in_db = Images.objects.all()
        self.assertEquals(images_in_db.count(), 5)
        self.assertEquals(images_in_db[0].id, 1)

        predictions_in_db = Sessions.objects.all()
        self.assertEquals(predictions_in_db.count(), 1)
        self.assertEquals(predictions_in_db[0].name, "set")


# If anyone can actually make these tests work that would be much appreciated. I am not sure how to make use of the
# test_annotations.json file to send it as json as an input for the method

# class TestLinkAnnotations(TestCase):
#     def test_basic_link_annotations(self):
#         csv_to_string = ""
#         with open("SECAAlgo/tests/test_helper_method_files/save_csv_example_file.csv", "r") as csv_file:
#             reader = csv.reader(csv_file)
#             for next_line in reader:
#                 if csv_to_string == "":
#                     csv_to_string = next_line[0] + "," + next_line[1] + "," + next_line[2]
#                 else:
#                     csv_to_string = csv_to_string + "\n" + next_line[0] + "," + next_line[1] + "," + next_line[2]
#
#         res_string, successful_save, session_id = save_csv_predictions({"data_set": csv_to_string,
#                                                                         "dataset_name": "set", "username": []})
#
#         annotation_to_string = ""
#         with open("SECAAlgo/tests/test_helper_method_files/test_annotations.json") as annotation_file:
#             for line in annotation_file:
#                 print(line)
#                 if annotation_to_string == "":
#                     annotation_to_string = line
#                 else:
#                     annotation_to_string = annotation_to_string + line
#
#             annotation_file.close()
#
#         link_annotations(annotation_to_string, session_id)
#
#         annotations_in_db = Annotations.objects.all()
#         images_in_db = Images.objects.all()
#
#         self.assertEquals(annotations_in_db.count(), 5)
#         self.assertEquals(annotations_in_db[0].image, images_in_db[3])
#         self.assertEquals(annotations_in_db[0].annotation, "Missile")
#         self.assertEquals(annotations_in_db[1].annotation, "Stealth-y ness")
#         self.assertEquals(annotations_in_db[1].bounding_box_coordinates, "[2, 3, 4, 5]")
#         self.assertEquals(annotations_in_db[2].weight, 42)
#
#     def test_link_annotations_multiple_csv(self):
#         csv_to_string = ""
#         with open("SECAAlgo/tests/test_helper_method_files/save_csv_example_file.csv", "r") as csv_file:
#             reader = csv.reader(csv_file)
#             for next_line in reader:
#                 if csv_to_string == "":
#                     csv_to_string = next_line[0] + "," + next_line[1] + "," + next_line[2]
#                 else:
#                     csv_to_string = csv_to_string + "\n" + next_line[0] + "," + next_line[1] + "," + next_line[2]
#
#         res_1, save_1, session_id_1 = save_csv_predictions({"data_set": csv_to_string, "dataset_name": "set_1",
#                                                             "username": []})
#
#         res_2, save_2, session_id_2 = save_csv_predictions({"data_set": csv_to_string, "dataset_name": "set_2",
#                                                             "username": []})
#
#         with open ("SECAAlgo/tests/test_helper_method_files/test_annotations.json") as annotation_file:
#             link_annotations(global_annotations, session_id_2)
#             annotation_file.close()
#
#         annotations_in_db = Annotations.objects.all()
#         predictions_in_db = Sessions.objects.all()
#
#         self.assertEquals(annotations_in_db.count(), 5)
#         self.assertEquals(annotations_in_db[0].image, predictions_in_db[1].images.all()[3])
#         self.assertNotEquals(annotations_in_db[0].image, predictions_in_db[0].images.all()[3])
#         self.assertEquals(annotations_in_db[1].annotation, "Stealth-y ness")
#         self.assertEquals(annotations_in_db[1].bounding_box_coordinates, "[2, 3, 4, 5]")


class TestMakeAnnotations(TestCase):
    def test_make_annotations_basic(self):
        annotation = make_annotations("SECAAlgo/tests/test_helper_method_files/test_annotations.json")
        self.assertEquals(annotation, {
            "Image_4": {
                "Missile": 1,
                "Stealth-y ness": 1
            },
            "Image_2": {
                "leg": 1,
                "other leg": 1
            },
            "Image_5": {
                "nuke": 1
            }
        })

    def test_make_annotations_basic(self):
        annotation = make_annotations("SECAAlgo/tests/test_helper_method_files/empty_annotations.json")
        self.assertEquals(annotation, {})


class TabularRepresentationTests(TestCase):
    def test_tabular_representation_basic_use(self):
        tabular_representation = get_tabular_representation("SECAAlgo/tests/test_helper_method_files/test_annotations"
                                                            ".json",
                                                            "SECAAlgo/tests/test_helper_method_files"
                                                            "/save_csv_example_file.csv")

        self.assertEquals(len(tabular_representation['image_name']), 3)
        self.assertEquals(tabular_representation.loc[0, 'image_name'], "Image_4")
        self.assertEquals(tabular_representation.loc[0, 'true_label'], "B-2 spirit stealth bomber")
        self.assertEquals(tabular_representation.loc[0, 'classification_check'], "Misclassified")
        self.assertEquals(tabular_representation.loc[1, 'classification_check'], "Correctly classified")
        self.assertEquals(tabular_representation.loc[0, 'Missile'], 1)
        self.assertEquals(tabular_representation.loc[1, 'Missile'], 0)
        self.assertEquals(tabular_representation.loc[2, 'Missile'], 0)


class TabularClassificationRuleMiningTest(TestCase):
    def test_tab_rule_mining(self):
        rule_tab_rep = get_tabular_representation_rule_mining(
            "SECAAlgo/tests/test_helper_method_files/test_annotations.json",
            "SECAAlgo/tests/test_helper_method_files/save_csv_example_file.csv",
            ["leg", "Missile", "Stealth-y ness", "nuke", "other leg",
             "Missile AND Stealth-y ness"])

        self.assertEquals(len(rule_tab_rep['image_name']), 3)
        self.assertEquals(rule_tab_rep.loc[0, 'image_name'], "Image_4")
        self.assertEquals(rule_tab_rep.loc[0, 'true_label'], "B-2 spirit stealth bomber")
        self.assertEquals(rule_tab_rep.loc[0, 'classification_check'], "Misclassified")
        self.assertEquals(rule_tab_rep.loc[1, 'classification_check'], "Correctly classified")
        self.assertEquals(rule_tab_rep.loc[0, 'Missile'], 1)
        self.assertEquals(rule_tab_rep.loc[1, 'Missile'], 0)
        self.assertEquals(rule_tab_rep.loc[2, 'Missile'], 0)
        self.assertEquals(rule_tab_rep.loc[0, 'Missile AND Stealth-y ness'], 1)
        self.assertEquals(rule_tab_rep.loc[1, 'Missile AND Stealth-y ness'], 0)
        self.assertEquals(rule_tab_rep.loc[2, 'Missile AND Stealth-y ness'], 0)
        self.assertTrue("Image_4" in rule_tab_rep['image_name'].values and
                        "Image_2" in rule_tab_rep['image_name'].values and
                        "Image_5" in rule_tab_rep['image_name'].values)
        self.assertTrue("B-2 spirit stealth bomber" in rule_tab_rep['true_label'].values and
                        "table" in rule_tab_rep['true_label'].values)
        self.assertTrue("table" in rule_tab_rep['predicted_label'].values and
                        "nuclear missile" in rule_tab_rep['predicted_label'].values)
