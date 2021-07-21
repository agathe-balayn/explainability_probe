from django.urls import path, include
from rest_framework import routers
from .views import confusion_matrix, query_db, all_images_from_problem_view, data_all_images, query_all, \
    query_concepts_and_rules, data_overall_explanations, data_specific_explanations, \
    query_specific_images, images_matrix, NotesView, add_data, add_image, get_predictions, \
    get_f1, query_concept_matrix, query_scores



urlpatterns = [
    # Endpoints related to Images
    path('Images/allImages/', all_images_from_problem_view, name="allImages"),

    # Endpoints related to Matrix Interface
    path('Matrix/matrix/', confusion_matrix, name="matrix"),
    path('Matrix/images/', images_matrix, name="matrix_images"),

    # Endpoints related to Explore Interface
    path('Explore/data_all_images/', data_all_images, name="data_all_images"),
    path('Explore/data_overall_explanations/', data_overall_explanations, name="data_overall_explanations"),
    path('Explore/data_specific_explanations/', data_specific_explanations, name="data_specific_explanations"),

    # Endpoints related to Query Interface
    path('Query/query/', query_db, name="query"),
    path('Query/query_rules/', query_concepts_and_rules, name="query_rules"),
    path('Query/query_scores/', query_scores, name="query_scores"),
    path('Query/uquery/', query_all, name="uquery"),
    path('Query/query_specific/', query_specific_images, name="query_specific_images"),
    path('Query/query_concept_matrix/', query_concept_matrix, name="query_concept_matrix"),

    #Endpoints related to Notes
    path('notes/', NotesView.as_view(), name="notes_view"),
    path('UserProfile/predictions', get_predictions, name="get_predictions"),

    #Endpoints related to data upload
    path('add_data/', add_data, name="add_data"),
    path('add_image/', add_image, name="add_image_matrix"),

    path('f1_scores/', get_f1, name="f1_score_matrix"),
]
