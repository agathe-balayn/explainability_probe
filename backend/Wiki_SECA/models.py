from django.db import models
from SECAAlgo.models import Sessions

# Create your models here.

class Problem_wiki(models.Model):
    """
    The problem wiki model/database table stores the data relevant for a wiki instance.

    This entails four fields, namely: the image, the title of the image, the intro for the image, 
    and finally the corresponding session. 
    """
    session = models.ForeignKey(Sessions, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    intro = models.CharField(max_length=1000)
    image = models.CharField(max_length=100, null=True)


class Content_wiki(models.Model):
    """
    The content wiki model/database table stores the data relevant for additional content on a specific Problem.

    This entails five fields, namely: the problem in question, the name of the image class, the description, 
    the concepts, and finally the image itself.
    """
    problem_wiki = models.ForeignKey(Problem_wiki, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, primary_key=True)
    description = models.CharField(max_length=10000)
    concepts = models.CharField(max_length=1000)
    image = models.CharField(max_length=100)