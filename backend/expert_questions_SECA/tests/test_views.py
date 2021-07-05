import json
from unittest.mock import patch

import pandas as pd
from django.contrib.auth.models import User
from django.urls import resolve, reverse
from expert_questions_SECA.models import Question
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
from SECAAlgo.models import Images, Sessions
from UserSECA.models import SECAUser


class GlobalSetUp(APITestCase):
    def setUp(self) -> None:
        # Making Session objects 
        image_1 = Images(image_name="headphones.png", actual_image="airpods", predicted_image="galaxy_buds")
        image_1.save()

        exampleUser_1 = User(username="Anthony", password="safe_password")
        exampleUser_1.save()
        secaUser_1 = SECAUser(user=exampleUser_1, is_developer=False, notes="some note here")
        secaUser_1.save()

        session_1 = Sessions(name="session_1")
        session_1.save()
        session_1.images.add(image_1)
        session_1.users.add(secaUser_1)

        self.session_1 = session_1

        image_2 = Images(image_name="keyboard.png", actual_image="keyboard", predicted_image="keyboard")
        image_2.save()
        
        exampleUser_2 = User(username="Bob", password="safe_password")
        exampleUser_2.save()
        secaUser_2 = SECAUser(user=exampleUser_2, is_developer=True, notes="some note here")
        secaUser_2.save()

        session_2 = Sessions(name="session_2")
        session_2.save()
        session_2.images.add(image_2)
        session_2.users.add(secaUser_2)

        self.session_2 = session_2


        # Making a Question object
        question_1 = Question.objects.create(prediction = session_1, question = "knock knock?", answer = "who's there?")
        question_2 = Question.objects.create(prediction = session_2, question = "?", answer = "?")
        question_1.save()
        question_2.save()

        self.question_1 = question_1
        self.question_2 = question_2

        return super().setUp()

    def tearDown(self) -> None:
        return super().tearDown()

class TestQuestionViews(GlobalSetUp):
    def test_delete_sucess(self):        
        response = self.client.delete("/api/Expert/questions/?session_id=1&question=knock knock?")
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(json.loads(response.content), {"questions":"deleted"})

        all_questions = Question.objects.all()
        self.assertEquals(all_questions[0], self.question_2)
    
    def test_delete_failure(self):
        response = self.client.delete("/api/Expert/questions/?session_id=13&question=knock knock?")
        self.assertEquals(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_success(self):
        response = self.client.get("/api/Expert/questions/?session_id=1")
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        expected_result = {
            "questions": [{'question': 'knock knock?', 'answer': "who's there?"}]
        }
        self.assertEquals(json.loads(response.content), expected_result)
    
    def test_get_failure(self):
        response = self.client.get("/api/Expert/questions/?session_id=12")
        self.assertEquals(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_post_success(self):
        response = self.client.post("/api/Expert/questions/", {"session_id": 1, "question": "knock knock?", "answer": "hi!"},
            format="json")
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(json.loads(response.content), {'questions': 'success'})
