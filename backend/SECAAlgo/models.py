from statistics import mode
from django.db import models
from numpy import blackman
from django.db.models import AutoField
from UserSECA.models import SECAUser


# Create your models here.
class Images(models.Model):
    id = models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    image_name = models.CharField(max_length=50)
    actual_image = models.CharField(max_length=100)
    predicted_image = models.CharField(max_length=100)


class Sessions(models.Model):
    users = models.ManyToManyField(SECAUser)
    images = models.ManyToManyField(Images)
    name = models.CharField(max_length=100, unique=True, default="")


class Annotations(models.Model):
    #id = models.AutoField(primary_key=True, default=0)
    image = models.ForeignKey(Images, on_delete=models.CASCADE)
    annotation = models.CharField(max_length=50)
    bounding_box_coordinates = models.CharField(max_length=50)
    weight = models.IntegerField()
    #heatmap_id = models.CharField(max_length=50)
    reason = models.CharField(max_length=300, blank=True, null=True)


class Rules(models.Model):
    antecedents = models.CharField(max_length=200)
    consequents = models.CharField(max_length=200, blank=True)

    antecedent_support = models.FloatField(blank=True, null=True)
    antecedent_len = models.IntegerField(blank=True, null=True)
    p_value = models.FloatField(blank=True, null=True)
    cramers_value = models.FloatField(blank=True, null=True)
    class_frequencies = models.TextField(blank=True)

    consequent_support = models.FloatField(blank=True, null=True)
    rule_support = models.FloatField(blank=True, null=True)
    rule_confidence = models.FloatField(blank=True, null=True)
    lift = models.FloatField(blank=True, null=True)
    leverage = models.FloatField(blank=True, null=True)
    conviction = models.FloatField(blank=True, null=True)


class Notes(models.Model):
    content = models.TextField(null=True, blank=True)
    user = models.ManyToManyField(SECAUser)
    session = models.ManyToManyField(Sessions)
