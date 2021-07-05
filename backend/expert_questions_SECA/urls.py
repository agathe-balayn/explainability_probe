from django.urls import path, include
from rest_framework import routers
from .views import QuestionsAndAnswers

urlpatterns = [
    path('questions/', QuestionsAndAnswers.as_view(), name="questions_and_answers")
]