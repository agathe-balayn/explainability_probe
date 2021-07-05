import json
from unittest.mock import patch

import pandas as pd
from django.contrib.auth.models import User
from django.urls import resolve, reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
from SECAAlgo.models import Images, Sessions
from UserSECA.models import SECAUser
from Wiki_SECA.models import Content_wiki, Problem_wiki

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

        # Making a Problem_Wiki instance
        problem_wiki_1 = Problem_wiki.objects.create(session = session_1, title = "Title 1", intro = "some introduction",
                                                        image = "American Goldfinch.png")
        problem_wiki_1.save()
        self.problem_wiki_1 = problem_wiki_1

        # Making a Content_Wiki instance
        content_wiki = Content_wiki.objects.create(problem_wiki = problem_wiki_1, name="Content wiki", description="some description",
                                                        concepts="some concepts", image="American Goldfinch.png")
        content_wiki.save()
        self.content_wiki = content_wiki

        return super().setUp()
    
    def tearDown(self) -> None:
        return super().tearDown()

class TestQuestionViews(GlobalSetUp):
    def test_get(self):
        response = self.client.get("/api/Wiki/expertBackground/?session_id=1")
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(json.loads(response.content)["title"], "Title 1")
        self.assertEquals(json.loads(response.content)["intro"], "some introduction")
        self.assertEquals(json.loads(response.content)["titles"], ['Class', 'General Description', 'Expected concepts', 'Example Image'])
        self.assertIsNotNone(json.loads(response.content)["contents"])
    
    def test_post(self):
        response = self.client.post(reverse("expert_background"), {
            "file": "no change",
            "session_id": "1",
            "className": "new_name",
            "description":"new_description",
            "concepts": "new_concepts",
        }, format="json")
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        all_content = Content_wiki.objects.all()

        self.assertEquals(all_content[1].name, "new_name")
        self.assertEquals(all_content[1].description, "new_description")
        self.assertEquals(all_content[1].concepts, "new_concepts")
        self.assertEquals(all_content[1].image, "new_name.png")
        self.assertEquals(all_content[1].problem_wiki, self.problem_wiki_1)

    def test_put(self):
        response = self.client.put(reverse("updateTitleIntro"), {
            "session_id": 1,
            "title": "new_title",
            "intro": "new_intro",
        }, format="json")
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        
        all_problems = Problem_wiki	.objects.all()

        self.assertEquals(all_problems[0].title, "new_title")
        self.assertEquals(all_problems[0].intro, "new_intro")

    def test_delete(self):
        response = self.client.delete("/api/Wiki/remove_wiki/?session_id=1&class=Content wiki")
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        all_content = Content_wiki.objects.all()
        self.assertEquals(len(all_content), 0)
        
        