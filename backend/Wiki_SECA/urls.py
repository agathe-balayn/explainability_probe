from django.urls import path, include
from rest_framework import routers
from .views import WikiView

urlpatterns = [
    path('remove_wiki/', WikiView.as_view(), name="remove_wiki"),
    path('add_wiki/', WikiView.as_view(), name="add_wiki"),
    path('expertBackground/', WikiView.as_view(), name="expert_background"),
    path('updateTitleIntro/', WikiView.as_view(), name="updateTitleIntro"),
]