from django.contrib.auth.models import User
from django.test import TestCase
from SECAAlgo.models import Images, Sessions
from UserSECA.models import SECAUser
from Wiki_SECA.models import Content_wiki, Problem_wiki

class ModelSetUp(TestCase):
    def setUp(self) -> None:
        # Making two SECA users
        notes = "This user follows TDD"
        user_1 = User.objects.create_user(username="expert_1", password="expert")
        seca_user_exp_1 = SECAUser.objects.create(user=user_1, is_developer=False, notes=notes)
        user_1.seca_user = seca_user_exp_1
        user_1.save()

        user_2 = User.objects.create_user(username="expert_2", password="expert")
        seca_user_exp_2 = SECAUser.objects.create(user=user_2, is_developer=False)
        user_2.seca_user = seca_user_exp_2
        user_2.save()


        self.user_1 = user_1
        self.user_2 = user_2

        # Making some Images
        image_1 = Images.objects.create(image_name="image1.png", actual_image="monitor", predicted_image="tv")
        image_2 = Images.objects.create(image_name="image2.png", actual_image="laptop", predicted_image="laptop")
        image_3 = Images.objects.create(image_name="image3.png", actual_image="earphones", predicted_image="wire")
        image_4 = Images.objects.create(image_name="image4.png", actual_image="person", predicted_image="monkey")

        image_1.save()
        image_2.save()
        image_3.save()
        image_4.save()

        # Making Sessions object
        session1 = Sessions(name="session1")
        session1.save()
        session1.images.add(image_1, image_3)
        session1.users.add(seca_user_exp_1)

        session2 = Sessions(name="session2")
        session2.save()
        session2.images.add(image_1, image_2, image_4)
        session2.users.add(seca_user_exp_2)

        # Making a Problem_Wiki instance
        problem_wiki_1 = Problem_wiki.objects.create(session = session1, title = "Title 1", intro = "some introduction",
                                                        image = "image1, image2")

        problem_wiki_1.save()

        problem_wiki_2 = Problem_wiki.objects.create(session = session2, title = "Title 2", intro = "some introduction 2",
                                                        image = "image3, image 4")
        problem_wiki_2.save()

        # Making a Content_Wiki instance
        content_wiki = Content_wiki.objects.create(problem_wiki = problem_wiki_1, name="Content wiki", description="some description",
                                                        concepts="some concepts", image="image5, image2")
        content_wiki.save()


        self.problem_wiki_1 = problem_wiki_1
        self.problem_wiki_2 = problem_wiki_2
        self.content_wiki = content_wiki

        self.session_1 = session1
        self.session_2 = session2
        return super().setUp()

    def tearDown(self) -> None:
        return super().tearDown()

class TestProblemWikiModel(ModelSetUp):
    def test_constructor(self):
        # Constructor tests for Problem_wiki
        self.assertEquals(self.problem_wiki_1.session, self.session_1)
        self.assertEquals(self.problem_wiki_1.title, "Title 1")
        self.assertEquals(self.problem_wiki_1.intro, "some introduction")
        self.assertEquals(self.problem_wiki_1.image,  "image1, image2")

        self.assertEquals(self.problem_wiki_2.session, self.session_2)
        self.assertEquals(self.problem_wiki_2.title, "Title 2")
        self.assertEquals(self.problem_wiki_2.intro, "some introduction 2")
        self.assertEquals(self.problem_wiki_2.image, "image3, image 4")

        # Constructor tests for Content_wiki
        self.assertEquals(self.content_wiki.problem_wiki, self.problem_wiki_1)
        self.assertEquals(self.content_wiki.name, "Content wiki")
        self.assertEquals(self.content_wiki.description, "some description")
        self.assertEquals(self.content_wiki.concepts, "some concepts")
        self.assertEquals(self.content_wiki.image, "image5, image2")
