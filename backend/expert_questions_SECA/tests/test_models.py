from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.authtoken.models import Token
from SECAAlgo.models import Sessions, Images
from UserSECA.models import SECAUser
from expert_questions_SECA.models import Question

class TestQuestionModel(TestCase):
    def setUp(self) -> None:
        # Making a Session object
        image = Images(image_name="headphones.png", actual_image="airpods", predicted_image="galaxy_buds")
        image.save()

        exampleUser = User(username="Anthony", password="safe_password")
        exampleUser.save()
        secaUser = SECAUser(user=exampleUser, is_developer=False, notes="some note here")
        secaUser.save()

        session = Sessions(name="prediction_1")
        session.save()
        session.images.add(image)
        session.users.add(secaUser)

        self.session = session

        # Making a Question object
        question = Question.objects.create(prediction = session, question = "knock knock?", answer = "who's there?")
        
        self.question = question
        return super().setUp()

    def tearDown(self) -> None:
        return super().tearDown()
    
    def test_constructor(self):
        self.assertEquals(self.question.question, "knock knock?")
        self.assertEquals(self.question.answer, "who's there?")
        self.assertEquals(self.question.prediction, self.session)

    def test_setter(self):
        self.question.question = "is 42 the answer to life?"
        self.question.answer = "yes."
        self.assertEquals(self.question.question, "is 42 the answer to life?")
        self.assertEquals(self.question.answer, "yes.")


        # Making a Session object
        image = Images(image_name="cat.png", actual_image="cat", predicted_image="dog")
        image.save()

        exampleUser = User(username="Bob", password="safe_password")
        exampleUser.save()
        secaUser = SECAUser(user=exampleUser, is_developer=True, notes="some note here")
        secaUser.save()

        session2 = Sessions(name="prediction_2")
        session2.save()
        session2.images.add(image)
        session2.users.add(secaUser)

        self.question.prediction = session2
        self.assertEquals(self.question.prediction, session2)
