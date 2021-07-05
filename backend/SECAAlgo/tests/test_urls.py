from django.test import SimpleTestCase
from django.urls import resolve, reverse
from SECAAlgo.views import (all_images_from_problem_view, confusion_matrix,
                            data_all_images, query_all,
                            query_concepts_and_rules, query_db,
                            images_matrix, data_overall_explanations,
                            data_specific_explanations, query_specific_images, NotesView, get_predictions, 
                            add_data, add_image, get_f1)


class TestUrls(SimpleTestCase):
    def test_allImages_resolves(self):
        url = reverse('allImages')
        self.assertEquals(resolve(url).func, all_images_from_problem_view)

    def test_matrix_resolves(self):
        url = reverse("matrix")
        self.assertEquals(resolve(url).func, confusion_matrix)
    
    def test_matrix_images_resolves(self):
        url = reverse("matrix_images")
        self.assertEquals(resolve(url).func, images_matrix)

    def test_explore_data_all_images_resolves(self):
        url = reverse("data_all_images")
        self.assertEquals(resolve(url).func, data_all_images)
    
    def test_explore_overall_explanations_resolves(self):
        url = reverse("data_overall_explanations")
        self.assertEquals(resolve(url).func, data_overall_explanations)
    
    def test_explore_data_specific_explanations_resolves(self):
        url = reverse("data_specific_explanations")
        self.assertEquals(resolve(url).func, data_specific_explanations)

    def test_query_resolves(self):
        url = reverse("query")
        self.assertEquals(resolve(url).func, query_db)
    
    def test_query_resolves(self):
        url = reverse("query_rules")
        self.assertEquals(resolve(url).func, query_concepts_and_rules)
    
    def test_query_resolves(self):
        url = reverse("uquery")
        self.assertEquals(resolve(url).func, query_all)
    
    def test_query_specific_images_resolves(self):
        url = reverse("query_specific_images")
        self.assertEquals(resolve(url).func, query_specific_images)

    def test_notes_view_resolves(self):
        url = reverse("notes_view")
        self.assertEquals(resolve(url).func.view_class, NotesView)
    
    def test_get_predictions_resolves(self):
        url = reverse("get_predictions")
        self.assertEquals(resolve(url).func, get_predictions)

    def test_add_data_resolves(self):
        url = reverse("add_data")
        self.assertEquals(resolve(url).func, add_data)
    
    def test_add_image_resolves(self):
        url = reverse("add_image_matrix")
        self.assertEquals(resolve(url).func, add_image)
    
    def test_f1_scores_resolves(self):
        url = reverse("f1_score_matrix")
        self.assertEquals(resolve(url).func, get_f1)
    


