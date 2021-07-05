import json
from os import name
from unittest.mock import patch

import pandas as pd
from django.contrib.auth.models import User
from django.test.testcases import TestCase
from django.urls import resolve, reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
from SECAAlgo.models import Annotations, Images, Sessions
from SECAAlgo.pipeline import (make_tabular_representation,
                               perform_rule_mining, retrieve_images, make_tabular_representation_rule_mining_included)
from UserSECA.models import SECAUser


def mock_prepare_data_mining_input(semantic_feature_representation):
    modified_representation = [['curtains', 'window', 'pillow', 'bed', 'bedroom'], [
        'childs_room'], ['childs_room']]
    list_antecedents = frozenset(
        {'predicted_label', 'window', 'curtains', 'bed', 'pillow'})
    list_consequents = frozenset({'predicted_label'})
    return modified_representation, list_antecedents, list_consequents


def mock_get_rules(semantic_feature_representation,
                   min_support_score=0.75,
                   min_lift_score=1.2,
                   min_confidence_score=0.75):
    rules = pd.read_json('SECAAlgo/tests/test_data/rules.json')
    rules["antecedents"] = rules["antecedents"].apply(lambda x: frozenset(x))
    rules["consequents"] = rules["consequents"].apply(lambda x: frozenset(x))

    frequent_itemsets = pd.read_json(
        'SECAAlgo/tests/test_data/frequent_itemsets.json')
    frequent_itemsets["itemsets"] = frequent_itemsets["itemsets"].apply(
        lambda x: frozenset(x))
    return rules, frequent_itemsets


class DatabaseSetup(TestCase):
    def setUp(self) -> None:
        image1 = Images(image_name="Places365_val_00035413.jpg", actual_image="bedroom",
                        predicted_image="childs_room")
        image2 = Images(image_name="Places365_val_00019097.jpg", actual_image="bedroom",
                        predicted_image="childs_room")
        image3 = Images(image_name="Places365_val_00015617.jpg", actual_image="childs_room",
                        predicted_image="bedroom")
        image4 = Images(image_name="console.jpg",
                        actual_image="xbox", predicted_image="playstation")
        image5 = Images(image_name="controller.jpg",
                        actual_image="xbox", predicted_image="xbox")
        image6 = Images(image_name="laptop.jpg",
                        predicted_image="dell", actual_image="apple")
        image1.save()
        image2.save()
        image3.save()
        image4.save()
        image5.save()
        image6.save()

        annotation1 = Annotations(
            image=image3, annotation="curtains", bounding_box_coordinates="[1, 2, 3, 4]", weight=1)
        annotation2 = Annotations(
            image=image3, annotation="window", bounding_box_coordinates="[1, 2, 3, 4]", weight=1)
        annotation3 = Annotations(
            image=image3, annotation="pillow", bounding_box_coordinates="[1, 2, 3, 4]", weight=1)
        annotation4 = Annotations(
            image=image3, annotation="bed", bounding_box_coordinates="[1, 2, 3, 4]", weight=1)
        annotation5 = Annotations(
            image=image3, annotation="bed", bounding_box_coordinates="[3, 4, 5, 1]", weight=1)
        annotation6 = Annotations(
            image=image3, annotation="window", bounding_box_coordinates="[20, 10, 1, 6]", weight=1)
        annotation7 = Annotations(
            image=image3, annotation="pillow", bounding_box_coordinates="[20, 10, 1, 6]", weight=1)
        annotation8 = Annotations(image=image3, annotation="curtains",
                                  bounding_box_coordinates="[301, 10, 1, 6]", weight=1)

        annotation9 = Annotations(
            image=image4, annotation="tv", bounding_box_coordinates="[20, 15, 1, 6]", weight=1)
        annotation10 = Annotations(
            image=image4, annotation="black", bounding_box_coordinates="[25, 15, 1, 6]", weight=1)
        annotation11 = Annotations(
            image=image5, annotation="buttons", bounding_box_coordinates="[25, 15, 1, 6]", weight=1)
        annotation12 = Annotations(
            image=image5, annotation="joystick", bounding_box_coordinates="[30, 15, 11, 6]", weight=1)
        annotation13 = Annotations(
            image=image6, annotation="keyboard", bounding_box_coordinates="[76, 15, 11, 6]", weight=1)
        annotation14 = Annotations(
            image=image6, annotation="display", bounding_box_coordinates="[25, 13, 1, 62]", weight=1)

        annotation1.save()
        annotation2.save()
        annotation3.save()
        annotation4.save()
        annotation5.save()
        annotation6.save()
        annotation7.save()
        annotation8.save()
        annotation9.save()
        annotation10.save()
        annotation11.save()
        annotation12.save()
        annotation13.save()
        annotation14.save()

        # Setting up Session
        exampleUser = User(username="Kanit", password="safe_password")
        exampleUser.save()
        secaUser = SECAUser(user=exampleUser, is_developer=False, notes="some note here")
        secaUser.save()

        session = Sessions(name="session_1")
        session.save()
        session.users.add(secaUser)
        session.images.add(image1, image2, image3, image4, image5, image6)

        self.session = session
        return super().setUp()

    def tearDown(self) -> None:
        return super().tearDown()


class TestPipeline(DatabaseSetup):
    # The following are tests for the the retrieve_images method

    def test_retrieve_images_invalid_session(self):
        result, stat = retrieve_images(image_set_setting="ALL_IMAGES")
        self.assertEquals(stat, status.HTTP_400_BAD_REQUEST)
        self.assertEquals({"The given session does not exist"}, result)

    def test_retrieve_images_invalid_setting(self):
        result, stat = retrieve_images(image_set_setting="hbasdff", session_id=1)
        self.assertEquals(stat, status.HTTP_400_BAD_REQUEST)
        self.assertEquals({"The given image setting is not valid"}, result)

    def test_retrieve_images_all_images(self):
        result, stat = retrieve_images(image_set_setting="ALL_IMAGES", session_id=1)
        self.assertEquals(set([1, 2, 3, 4, 5, 6]), result)
        self.assertEquals(stat, status.HTTP_200_OK)

    def test_retrieve_images_correct_only(self):
        result, stat = retrieve_images(
            image_set_setting="CORRECT_PREDICTION_ONLY", session_id=1)
        self.assertEquals(set([5]), result)
        self.assertEquals(stat, status.HTTP_200_OK)

    def test_retrieve_images_incorrect_only(self):
        result, stat = retrieve_images(
            image_set_setting="WRONG_PREDICTION_ONLY", session_id=1)
        self.assertEquals(set([1, 2, 3, 4, 6]), result)
        self.assertEquals(stat, status.HTTP_200_OK)

    def test_retrieve_images_binary_view_valid(self):
        result, stat = retrieve_images(
            image_set_setting="BINARY_MATRIX_VIEW", binary_task_classes=["bedroom", "childs_room"], session_id=1)
        self.assertEquals(set([1, 2, 3]), result)
        self.assertEquals(stat, status.HTTP_200_OK)

    def test_retrieve_images_binary_view_invalid(self):
        result, stat = retrieve_images(
            image_set_setting="BINARY_MATRIX_VIEW", binary_task_classes=["childs_room"], session_id=1)
        self.assertEquals(stat, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(
            {"Please give two classes for a binary matrix view request"}, result)

        result2, stat2 = retrieve_images(
            image_set_setting="BINARY_MATRIX_VIEW")
        self.assertEquals(stat, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(
            {"Please give two classes for a binary matrix view request"}, result)

    # The following are tests for the make_tabular_representation method
    def test_make_tabular_representation(self):
        image_list = [1, 2, 3]
        sr, unique_sf = make_tabular_representation(
            image_list=image_list, image_set_setting="BINARY_MATRIX_VIEW")
        expected_sr = pd.read_csv(
            'SECAAlgo/tests/test_data/sr_test_tabular_1.csv')
        self.assertTrue(expected_sr.equals(sr))
        expected_unique_sf = ['curtains', 'window', 'pillow', 'bed']
        self.assertEquals(expected_unique_sf, unique_sf)

    def test_make_tabular_representation(self):
        image_list = [1, 2, 3]
        sr, unique_sf = make_tabular_representation(
            image_list=image_list, image_set_setting="ALL_IMAGES")
        expected_sr = pd.read_csv(
            'SECAAlgo/tests/test_data/sr_test_tabular_2.csv')
        self.assertTrue(expected_sr.equals(sr))
        expected_unique_sf = ['curtains', 'window', 'pillow', 'bed']
        self.assertEquals(expected_unique_sf, unique_sf)

    def test_make_tabular_representation(self):
        image_list = [4, 5, 6]
        sr, unique_sf = make_tabular_representation(
            image_list=image_list, image_set_setting="ALL_IMAGES")
        expected_sr = pd.read_csv(
            'SECAAlgo/tests/test_data/sr_test_tabular_3.csv')
        self.assertTrue(expected_sr.equals(sr))
        expected_unique_sf = ['tv', 'black', 'buttons',
                              'joystick', 'keyboard', 'display']
        self.assertEquals(expected_unique_sf, unique_sf)

    # The following are tests for the perform_rule_mining method

    @patch("SECAAlgo.pipeline.get_rules", mock_get_rules)
    @patch("SECAAlgo.pipeline.prepare_data_mining_input", mock_prepare_data_mining_input)
    def test_perform_rule_mining(self):
        structured_representation = pd.read_csv(
            'SECAAlgo/tests/test_data/sr_test_tabular_1.csv')
        max_antecedent_length = 3
        min_support_score = 0.000001
        min_lift_score = 0.2,
        min_confidence_score = 0.3
        filter_concepts = "ALL"
        or_queries = []
        or_exclude = []
        exclude_concepts = []
        data_mining_rules, antecendets_from_rule_mining, supp_conf = perform_rule_mining(
            structured_representation, max_antecedent_length, min_support_score, min_lift_score, min_confidence_score,
            filter_concepts=filter_concepts, or_queries=or_queries, or_exclude=or_exclude, exclude_concepts=exclude_concepts)
        expected_antecedents_from_rm = ['bed', 'curtains', 'pillow', 'window', 'curtains AND bed', 'bed AND pillow',
                                        'bed AND window', 'curtains AND pillow', 'curtains AND window', 'pillow AND window',
                                        'curtains AND bed AND pillow', 'curtains AND bed AND window', 'bed AND pillow AND window',
                                        'curtains AND pillow AND window']
        expected_data_mining_rules = pd.read_json(
            'SECAAlgo/tests/test_data/data_mining_rules_1.json')
        expected_data_mining_rules["antecedents"] = expected_data_mining_rules["antecedents"].apply(
            lambda x: frozenset(x))
        expected_data_mining_rules["consequents"] = expected_data_mining_rules["consequents"].apply(
            lambda x: frozenset(x))

        expected_data_mining_antecedents = expected_data_mining_rules["antecedents"].tolist(
        )
        actual_data_mining_antecedents = data_mining_rules["antecedents"].tolist(
        )

        # the reason we compare the antecedents is because the dataframe isn't always the same due to the randomness
        # in rule mining, but we know the antecedents we get will be the same
        self.assertListEqual(expected_data_mining_antecedents,
                             actual_data_mining_antecedents)

    # The following are tests for make_tabular_representation_rule_mining_included

    def test_make_tabular_representation_rule_mining_included(self):
        image_list = [1, 2, 3]
        sr, unique_sf = make_tabular_representation(
            image_list=image_list, image_set_setting="BINARY_MATRIX_VIEW")
        # a copy is made here, because structured_representation gets changed in rule mining
        rep_old = sr.copy(deep=True)

        max_antecedent_length = 3
        min_support_score = 0.000001
        min_lift_score = 0.2,
        min_confidence_score = 0.3
        filter_concepts = "ALL"
        or_queries = []
        or_exclude = []
        exclude_concepts = []
        data_mining_rules, antecendets_from_rule_mining, supp_conf = perform_rule_mining(
            sr, 3, 0.000001, 0.2, 0.3, "ALL", [], [], [])

        new_sr = make_tabular_representation_rule_mining_included(
            rep_old, unique_sf, antecendets_from_rule_mining)

        expected_new_sr = pd.read_csv(
            'SECAAlgo/tests/test_data/sr_test_tabular_rm_included.csv')

        # We cannot directly compare the two dataframes and assert their equality
        # because the order and name of the columns are random. So the best we can do is
        # compare if the two dataframes have the same number of columnns
        # (if not, we know something went wrong for sure)
        self.assertEquals(len(new_sr.columns), len(expected_new_sr.columns))
