from django.db import models
from SECAAlgo.models import Sessions

# Create your models here.

class Question(models.Model):
    """
    The Question model represents the database table that stores questions and answers between Developer and 
    Expert users that take place over a set of images ie. a particular Session.

    Due to this, the Question model has three fields, those being the session/prediction, and the question
    and answer.
    """
    prediction = models.ForeignKey(Sessions, on_delete=models.CASCADE)
    question = models.CharField(max_length=10000)
    answer = models.CharField(max_length=10000, blank = True)