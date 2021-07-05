from django.test import SimpleTestCase
from django.urls import resolve, reverse, path, include
from UserSECA.views import UserViewSet, GetAuthToken, get_sessions_from_user
from rest_framework.test import APITestCase, URLPatternsTestCase

class TestUrls(SimpleTestCase):
    def test_auth_resolves(self):
        url = reverse("auth")
        self.assertEquals(resolve(url).func.view_class, GetAuthToken)
    
    def test_get_sessions_from_user_resolves(self):
        url = reverse("get_sessions")
        self.assertEquals(resolve(url).func, get_sessions_from_user)