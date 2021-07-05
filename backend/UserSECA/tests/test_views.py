from unittest.mock import patch

from django.contrib.auth.models import User
from django.urls import resolve, reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
from UserSECA.models import SECAUser
from SECAAlgo.models import Sessions, Images
import pandas as pd
import json

class GlobalSetUp(APITestCase):
    def setUp(self):
        django_user = User.objects.create_user(username="Bob", password="safe_password")
        notes = "This user follows TDD"
        seca_user = SECAUser.objects.create(user=django_user, is_developer=False, notes=notes)
        
        django_user.seca_user = seca_user
        django_user.save()

        self.test_user = django_user
        self.test_user_token = Token.objects.create(user = django_user)
        # self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)
        return super().setUp()

    def tearDown(self) -> None:
        return super().tearDown()

class TestAuthenticationViews(GlobalSetUp):
    def test_login_success(self):
        response = self.client.post("/auth/", {"username": "Bob", "password": "safe_password"})
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content)
        
        self.assertEquals(response_data["token"], self.test_user_token.key)
        self.assertEquals(response_data["user"]["seca_user"], {"is_developer": False})
        self.assertEquals(response_data["user"]["username"], "Bob")
    
    def test_login_wrong_password_failure(self):
        response = self.client.post("/auth/", {"username": "Bob", "password": "wrong_password"})
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(json.loads(response.content), {'non_field_errors': ['Unable to log in with provided credentials.']})
    
    def test_login_no_password_given_failure(self):
        response = self.client.post("/auth/", {"username": "Bob"})
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(json.loads(response.content), {'password': ['This field is required.']})

    def test_login_no_username_given_failure(self):
        response = self.client.post("/auth/", {"password": "1212312"})
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(json.loads(response.content), {'username': ['This field is required.']})

    def test_registration_developer(self):
        response = self.client.post("/api/UserSECA/users/", {"username": "Karen", "password": "12345", 
            "seca_user": {"is_developer": True}}, format="json")
        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        response_data = json.loads(response.content)

        self.assertEquals(response_data["username"], "Karen")
        self.assertEquals(response_data["seca_user"], {"is_developer": True})

    def test_registration_expert(self):
        response = self.client.post("/api/UserSECA/users/", {"username": "Karen2", "password": "12345", 
            "seca_user": {"is_developer": False}}, format="json")
        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        response_data = json.loads(response.content)

        self.assertEquals(response_data["username"], "Karen2")
        self.assertEquals(response_data["seca_user"], {"is_developer": False})

    def test_registration_same_username_failure(self):
        response = self.client.post("/api/UserSECA/users/", {"username": "Bob", "password": "12345", 
            "seca_user": {"is_developer": False}}, format="json")
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(json.loads(response.content), {'username': ['A user with that username already exists.']})

    def test_registration_no_password_given_failure(self):
        response = self.client.post("/api/UserSECA/users/", {"username": "Bob2", 
            "seca_user": {"is_developer": False}}, format="json")
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(json.loads(response.content), {'password': ['This field is required.']})

    def test_registration_no_username_given_failure(self):
        response = self.client.post("/api/UserSECA/users/", {"password": "1233454", 
            "seca_user": {"is_developer": False}}, format="json")
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(json.loads(response.content), {'username': ['This field is required.']})

    def test_registration_no_seca_user_data_given_failure(self):
        response = self.client.post("/api/UserSECA/users/", {"username": "Bob2", "password": "12345"}
                                                                        , format="json")
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(json.loads(response.content), {'seca_user': ['This field is required.']})
    
    def test_get_sessions_from_user_no_predictions(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.test_user_token.key)
        response = self.client.post(reverse("get_sessions"), {"user_id": 1})
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        expected_result = {
            'result': []
        }
        self.assertEquals(json.loads(response.content), expected_result)

    def test_get_sessions_from_user_has_predictions(self):
        # Setting up the session object
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.test_user_token.key)
        image = Images(image_name="router.png", actual_image="router", predicted_image="xbox")
        image.save()
        prediction = Sessions(name="prediction_1")
        prediction.save()
        prediction.images.add(image)
        prediction.users.add(self.test_user.seca_user)
        
        response = self.client.post(reverse("get_sessions"), {"user_id": 1})
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        expected_result = {
            "result": [{'id': 1, 'name': 'prediction_1'}]
        }
