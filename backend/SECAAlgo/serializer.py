from django.db.models.lookups import IsNull
from rest_framework import serializers
from .models import Images, Annotations, Sessions
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.db import transaction


class SerializerClassNotFoundException(Exception):
    pass


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Images
        fields = ["id", "image_name", "actual_image", "predicted_image"]


class AnnotationSerializer(serializers.ModelSerializer):
    image = ImageSerializer(required=False)

    class Meta:
        model = Annotations
        fields = ["image", "annotation", "bounding_box_coordinates", "weight", "reason"]


class SessionSerializer(serializers.ModelSerializer):
    image = ImageSerializer(required=False)

    class Meta:
        model = Sessions
        fields = ["id", "name", "image"]


def UniversalSerializer(input, in_class):
    if in_class == Images:
        return ImageSerializer(input, many=True)
    elif in_class == Sessions:
        return SessionSerializer(input, many=True)
    elif in_class == Annotations:
        return AnnotationSerializer(input, many=True)
    else:
        raise SerializerClassNotFoundException
