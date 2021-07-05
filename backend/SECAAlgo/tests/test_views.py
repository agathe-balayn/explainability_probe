from os import stat
from unittest.mock import patch

from django.contrib.auth.models import User
from django.urls import resolve, reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
from UserSECA.models import SECAUser
import pandas as pd
import json


def mock_save_csv_predictions_1(input_dir):
    return 'done', status.HTTP_200_OK, -1

def mock_save_csv_predictions_2(input_dir):
    return 'failed', status.HTTP_200_OK, 1


def mock_link_annotations(input_dir, csv_id):
    return "saved"


def mock_rule_mining_pipeline_explore_view(image_set_setting, session_id):
    if image_set_setting == "CORRECT_PREDICTION_ONLY":
        mock_data_res = "data_correct_predictions"
    elif image_set_setting == "WRONG_PREDICTION_ONLY":
        mock_data_res = "data_wrong_prediction"
    else:
        mock_data_res = "data_all_images"
    return mock_data_res, "supp_conf", status.HTTP_200_OK


def mock_execute_rule_mining_pipeline_matrix_view(image_set_setting,
                                                  max_antecedent_length, min_support_score,
                                                  min_lift_score, min_confidence_score):
    return "some data", "supp_conf", status.HTTP_200_OK


def mock_query_classes(input):
    return "some data", status.HTTP_200_OK


def mock_query_rules(input):
    return "some data", status.HTTP_200_OK


def mock_universal_query(input):
    return "some data", status.HTTP_200_OK

def mock_get_confusion_matrix_data(session_id):
    return "a lot of data", status.HTTP_200_OK

def mock_get_matrix_images(class_A, class_B, session_id):
    return "images", status.HTTP_200_OK

class GlobalSetUp(APITestCase):
    def setUp(self):
        # setting up a developer user
        user_d = User.objects.create_user(
            username="developer", password="developer")
        seca_user_developer = SECAUser.objects.create(
            user=user_d, is_developer=True)
        user_d.seca_user = seca_user_developer
        user_d.save()
        self.developer_token = Token.objects.create(user=user_d)
        self.developer = user_d

        # self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)
        # setting up an expert user
        user_e = User.objects.create_user(username="expert", password="expert")
        seca_user_expert = SECAUser.objects.create(
            user=user_e, is_developer=False)
        user_e.seca_user = seca_user_expert
        user_e.save()
        self.expert_token = Token.objects.create(user=user_e)
        self.expert = user_e

        return super().setUp()

    def tearDown(self) -> None:
        return super().tearDown()


# class TestMiscViews(GlobalSetUp):
    # TODO: fix these tests after the make annotations and such got changed
    # @patch("SECAAlgo.views.add_data", mock_save_csv_predictions)
    # def test_save_csv_user_authenticated(self):
    #     self.client.credentials(
    #         HTTP_AUTHORIZATION="Token " + self.developer_token.key)
    #     with open("SECAAlgo/tests/test_helper_method_files/test_annotations.json") as f:
    #         response = self.client.post(reverse('add_data'),
    #                                     {"dataSetName": "p_name", "userName": None, "data_set": None,
    #                                      "annotations": json.load(f)}, format='json')
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #
    # def test_save_csv_user_not_authenticated(self):
    #     with open("SECAAlgo/tests/test_helper_method_files/test_annotations.json") as f:
    #         response = self.client.post(reverse('add_data'), {"dataSetName": "p_name", "userName": None, "data_set": None,
    #                                                           "annotations": json.load(f)}, format='json')
    #     self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # Deprecated views
    # @patch("SECAAlgo.views.link_annotations", mock_link_annotations)
    # def test_set_annotations_user_authenticated(self):
    #     self.client.credentials(
    #         HTTP_AUTHORIZATION="Token " + self.developer_token.key)
    #     response = self.client.get(reverse('set_annotations'))
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)

    # def test_set_annotations_user_not_authenticated(self):
    #     response = self.client.get(reverse('set_annotations'))
    #     self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestExploreViews(GlobalSetUp):
    @patch("SECAAlgo.views.execute_rule_mining_pipeline", mock_rule_mining_pipeline_explore_view)
    def test_data_all_images_user_authenticated(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.developer_token.key)
        response = self.client.get(reverse('data_all_images'))
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        expected_result = {
            "data": "data_all_images"
        }
        self.assertEquals(json.loads(response.content),
                          expected_result)

    @patch("SECAAlgo.views.execute_rule_mining_pipeline", mock_rule_mining_pipeline_explore_view)
    def test_data_all_images_user_not_authenticated(self):
        response = self.client.get(reverse('data_all_images'))
        self.assertEquals(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("SECAAlgo.views.execute_rule_mining_pipeline", mock_rule_mining_pipeline_explore_view)
    def test_data_overall_explanations_correct_predictions(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.developer_token.key)
        response = self.client.post(reverse("data_overall_explanations"),
                                    {"IMAGE_SET_SETTING": "CORRECT_PREDICTION_ONLY",
                                     "session_id": 0})
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        expected_result = {
            "result": "data_correct_predictions"
        }
        self.assertEquals(json.loads(response.content),
                          expected_result)

    @patch("SECAAlgo.views.execute_rule_mining_pipeline", mock_rule_mining_pipeline_explore_view)
    def test_data_overall_explanations_wrong_predictions(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.developer_token.key)
        response = self.client.post(reverse("data_overall_explanations"),
                                    {"IMAGE_SET_SETTING": "WRONG_PREDICTION_ONLY",
                                     "session_id": 0})
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        expected_result = {
            "result": "data_wrong_prediction"
        }
        self.assertEquals(json.loads(response.content),
                          expected_result)

    @patch("SECAAlgo.views.execute_rule_mining_pipeline", mock_rule_mining_pipeline_explore_view)
    def test_data_overall_explanations_all_images(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.developer_token.key)
        response = self.client.post(reverse("data_overall_explanations"), {"IMAGE_SET_SETTING": "ALL_IMAGES",
                                                                           "session_id": 0})
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        expected_result = {
            "result": "data_all_images"
        }
        self.assertEquals(json.loads(response.content),
                          expected_result)


class TestMatrixViews(GlobalSetUp):
    @patch("SECAAlgo.views.get_confusion_matrix_data", mock_get_confusion_matrix_data)
    def test_confusion_matrix(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.developer_token.key)
        response = self.client.get(reverse("matrix"), {"session_id": 1})
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(json.loads(response.content), "a lot of data")

    @patch("SECAAlgo.views.get_matrix_images", mock_get_matrix_images)
    def test_images_matrix(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.developer_token.key)
        response = self.client.get(reverse("matrix_images"), {"classA": "childs_room", "classB": "hotel_room", "session_id": 1})
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(json.loads(response.content), "images")

    def test_images_matrix_key_error(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.developer_token.key)
        response = self.client.get(reverse("matrix_images"), {"classA": "childs_room"})
        self.assertEquals(response.status_code, status.HTTP_417_EXPECTATION_FAILED)
    
    @patch("SECAAlgo.views.execute_rule_mining_pipeline", mock_rule_mining_pipeline_explore_view)
    def test_data_all_images(self):
        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.developer_token.key)        
        response = self.client.get(reverse("data_all_images"), {"session_id": 1})
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(json.loads(response.content), {"data": "data_all_images"})

    @patch("SECAAlgo.views.save_csv_predictions", mock_save_csv_predictions_1)
    def test_add_data(self):
        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.developer_token.key)
        response = self.client.post(reverse("add_data"), {"dummy":"data"})
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(json.loads(response.content), "done")

    @patch("SECAAlgo.views.link_annotations", mock_link_annotations)
    @patch("SECAAlgo.views.save_csv_predictions", mock_save_csv_predictions_2)
    def test_add_data(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.developer_token.key)
        response = self.client.post(reverse("add_data"), {"dummy":"data"})
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(json.loads(response.content), "failed")



class TestImageViews(GlobalSetUp):
    def test_all_images_from_problem_view_no_session(self):
        response = self.client.get(reverse("allImages"), {"amount": 1, "problem": 2})
        self.assertEquals(response.status_code, status.HTTP_404_NOT_FOUND)

class TestQueryViews(GlobalSetUp):
    @patch("SECAAlgo.views.query_classes", mock_query_classes)
    def test_query_db(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.developer_token.key)
        response = self.client.post(reverse("query"))
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        actual_data = json.loads(response.content)
        self.assertEquals("some data", actual_data)

    @patch("SECAAlgo.views.query_rules", mock_query_rules)
    def test_query_concepts_and_rules(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.developer_token.key)
        response = self.client.post(reverse("query_rules"))
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        actual_data = json.loads(response.content)
        self.assertEquals("some data", actual_data)

    @patch("SECAAlgo.views.universal_query", mock_universal_query)
    def test_query_all(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.developer_token.key)
        response = self.client.post(reverse("uquery"))
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        actual_data = json.loads(response.content)
        self.assertEquals("some data", actual_data)
