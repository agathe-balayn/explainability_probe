import json
from unittest.mock import patch

import pandas as pd
from django.contrib.auth.models import User
from django.test.testcases import TestCase
from django.urls import resolve, reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
from SECAAlgo.models import Annotations, Images, Sessions
from SECAAlgo.pipeline import (make_tabular_representation,
                               perform_rule_mining, retrieve_images, make_tabular_representation_rule_mining_included)
from UserSECA.models import SECAUser
from SECAAlgo.confusion_matrix_methods import (get_confusion_matrix_data, get_matrix_images, calculate_f1_scores)

class DatabaseSetup(TestCase):
    def setUp(self) -> None:
        image = Images(image_name="exampleName", actual_image="real", predicted_image="real")
        image.save()

        image2 = Images(image_name="name2", actual_image="real_image", predicted_image="not_real")
        image2.save()

        exampleUser = User(username="Bob", password="safe_password")
        exampleUser.save()
        secaUser = SECAUser(user=exampleUser, is_developer=False, notes="some note here")
        secaUser.save()

        session = Sessions(name="session_1")
        session.save()
        session.images.add(image)
        session.images.add(image2)
        session.users.add(secaUser)
        return super().setUp()
    
    def tearDown(self) -> None:
        return super().tearDown()

class TestConfusionMatrixMethods(DatabaseSetup):
    def test_get_confusion_matrix_data(self):
        result, stat = get_confusion_matrix_data(session_id = 1)
        self.assertEquals(stat, status.HTTP_200_OK)
        self.assertEquals(result["categories"][0], "real")
        self.assertEquals(result["categories"][1], "real_image")
        self.assertEquals(result["categories"][2], "not_real")
        self.assertEquals(result["matrix (absolute)"][0], [1, 0, 0])
        self.assertEquals(result["matrix (absolute)"][1], [0, 0, 1])
        self.assertEquals(result["matrix (absolute)"][2], [0, 0, 0])
        self.assertEquals(result["num_images"], 2)

    def test_get_matrix_images_fails(self):
        # It is very difficult to actually test the success case for this method.
        # The reason is this: the method looks for images in the Images directory in a folder with the same
        # name as the session name corresponding to the session id given. We find it quite difficult to mock
        # the image reading from a folder. 
        # Therefore, only the failure has been tested for now, which the case when an invalid sesion id is given. 
        result, stat = get_matrix_images("real", "not_real", 10)
        self.assertEquals(stat, status.HTTP_417_EXPECTATION_FAILED)
        self.assertEquals(result, "You are trying to get information from a prediction set that does not exist")
    
    def test_calculate_f1_scores(self):
        res, stat = calculate_f1_scores(1)
        self.assertEquals(stat, status.HTTP_200_OK)
        self.assertEquals(res[0], [0.])
        self.assertEquals(res[1], [1.])
        self.assertEquals(res[2], [0.])

    