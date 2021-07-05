from django.db.models.lookups import IsNull
from rest_framework import serializers
from .models import SECAUser
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.db import transaction

class SECAUserSerializer(serializers.ModelSerializer):
    """
    This serialiser is for the SECAUser model. The inner class Meta defines meta data. The serialiser only serialises
    the is_developer field of the SECAUser model as specified in the fields variable.
    """
    class Meta:
        model = SECAUser
        fields = ['is_developer']


class UserSerializer(serializers.ModelSerializer):
    """
    This serialiser is defined for the Django User model. It takes care of serialisation when returning data
    and also deals with deserialisation (with input validation built in).

    The inner class Meta specifies how serialisation should take place when returining data. 
    The serialised fields are: id, username, password, email and seca_user. The seca_user field is an alias
    for the FK to the SECAUser model, this is defined in the models.py file.

    The SECAUserSerializer is used to serialise the seca_user object that this User references. 
    """
    seca_user = SECAUserSerializer()

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'email', 'seca_user']
        extra_kwargs = {'password': {'write_only': True, 'required': True}}

    @transaction.atomic  # If in any row creation it fails, all other ones roll back
    def create(self, validated_data):
        """
        This method gets called for POST requests to the UserViewSet view. Given the validated data, this method then 
        extracts relevant information to populate the database with a new user. 

        :param: validated_data: Django performs input validation on the HTTP request data, and once that is validated
            this is given to the serialiser. 
        :return: 
            - new_user: The object representing the new user created in the database.
        """
        seca_user_data = validated_data.pop('seca_user')
        new_user = User.objects.create_user(**validated_data)
        is_developer = seca_user_data["is_developer"]
        seca_user = None
        if (is_developer):
            seca_user = SECAUser.objects.create(user=new_user,
                                                is_developer=True)
        else:
            seca_user = SECAUser.objects.create(user=new_user,
                                                is_developer=False
                                                )

        new_user.seca_user = seca_user
        new_user.save()
        # create token for this new user, so that the user may immediately log in
        Token.objects.create(user=new_user)

        return new_user