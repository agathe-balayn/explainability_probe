from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.authtoken.models import Token
from UserSECA.models import SECAUser


class TestUserSECAModel(TestCase):
    def setUp(self) -> None:
        django_user = User.objects.create_user(username="Bob", password="safe_password")
        notes = "This user follows TDD"
        seca_user = SECAUser.objects.create(user=django_user, is_developer=False, notes=notes)
        
        django_user.seca_user = seca_user
        django_user.save()

        self.test_user = django_user
        self.test_user_token = Token.objects.create(user = django_user)
        
        return super().setUp()

    def tearDown(self) -> None:
        return super().tearDown()

    def test_constructor(self):
        self.assertEquals(self.test_user.username, "Bob")
        # We cannot actually test the password, because each time we run setUp(), the user is recreated
        # and because Django hashes the password, we never get the same hashes.
        self.assertEquals(self.test_user.seca_user.is_developer, False)
        self.assertEquals(self.test_user.seca_user.notes, "This user follows TDD")
        self.assertIsNotNone(self.test_user_token)

    def test_setter(self):
        self.test_user.seca_user.is_developer = True
        self.test_user.seca_user.notes = "This user doesn't follow TDD"
        self.assertEquals(self.test_user.seca_user.is_developer, True)
        self.assertEquals(self.test_user.seca_user.notes, "This user doesn't follow TDD")