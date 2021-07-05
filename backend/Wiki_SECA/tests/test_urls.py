from django.test import SimpleTestCase
from django.urls import resolve, reverse, path, include
from Wiki_SECA.views import WikiView
from rest_framework.test import APITestCase, URLPatternsTestCase

class TestUrls(SimpleTestCase):
    def test_remove_wiki_resolves(self):
        url = reverse("remove_wiki")
        self.assertEquals(resolve(url).func.view_class, WikiView)
    
    def test_add_wiki_resolves(self):
        url = reverse("add_wiki")
        self.assertEquals(resolve(url).func.view_class, WikiView)

    def test_expert_background_resolves(self):
        url = reverse("expert_background")
        self.assertEquals(resolve(url).func.view_class, WikiView)
