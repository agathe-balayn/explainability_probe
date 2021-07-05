from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class SECAUser(models.Model):
    """
    This model is the database table for the users that register via the SECA Interface.
    As the default Django User model is limited in its parameters, the SECAUser model has a 1-to-1 FK a Django User.

    Moreover, the SECAUser has an additional field, namely the is_developer field, indicating if the user is a Developer or Expert.
    """
    user = models.OneToOneField(User, models.CASCADE, related_name="seca_user")
    is_developer = models.BooleanField()
