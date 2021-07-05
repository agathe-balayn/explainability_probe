from django.test import SimpleTestCase
from django.urls import resolve, reverse, path, include
from expert_questions_SECA.views import QuestionsAndAnswers
from rest_framework.test import APITestCase, URLPatternsTestCase


class TestUrls(SimpleTestCase):
    def test_auth_resolves(self):
        url = reverse("questions_and_answers")
        self.assertEquals(resolve(url).func.view_class, QuestionsAndAnswers)