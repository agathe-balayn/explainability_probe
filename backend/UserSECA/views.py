from django.db import models
from django.shortcuts import render
from rest_framework import viewsets
from .serializer import UserSerializer
from django.contrib.auth.models import User
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.authentication import TokenAuthentication
from UserSECA.models import SECAUser
from SECAAlgo.serializer import SessionSerializer
from SECAAlgo.models import Sessions
from rest_framework import status
from rest_framework.response import Response

class UserViewSet(viewsets.ModelViewSet):
    """
    This is a class based view, extending the abstract ModelViewSet in the Django-Rest-Framework.
    A ModelViewSet implements basic CRUD routes for GET, POST, UPDATE, DELETE HTTP requests. 

    queryset variable specifies what data that is to be used by the ViewSet
    serializer_class variable specifies what custom serializer to use when returning the data
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer


class GetAuthToken(ObtainAuthToken):
    """
    This is another class based view, extending the ObtainAuthToken class from Django-Rest-Framework
    This class allows the developer to implement the functionality for authentication via Tokens. 
    """

    def post(self, request, *args, **kwargs):
        """
        This endpoint responds to HTTP POST Requests. It is expected that the HTTP Request contains credentials 
        (username and password) in the body. The method checks if the provided credentials are correct, 
        and after verification, the Token corresponding to that user is queried. 

        :param request: The HTTP request object
        :return:
            - Response: HTTP Response object that contains the user data and the token 
            in the response body.
        """
        # Call default GetAuthToken that is defined by Django rest framework, here it will check for
        # given credentials and if they are indeed correct
        response = super(GetAuthToken, self).post(request, *args, **kwargs)
        # if they are correct, then we get the token, and the user that matches that token, and return both
        token = Token.objects.get(key=response.data['token'])
        user = User.objects.get(id=token.user_id)
        user_serializer = UserSerializer(user, many=False)
        return Response({'token': token.key, 'user': user_serializer.data})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([
    TokenAuthentication,
])
def get_sessions_from_user(self):
    """
    For a given user id, this endpoint returns a list of all the associated sessions

    :param: self: Represents the HTTP request
    :return: 
        - Response: HTTP Response with status set to 200 OK, and the body containing the session list. The data itself
        is serialised into JSON using the custom SessionSerializer.
    """
    user_id = self.data["user_id"]
    normalUser = User.objects.filter(id=user_id)[0]
    linked_sessions = Sessions.objects.filter(users=SECAUser.objects.filter(user = normalUser)[0]).all()

    # Serializes the filtered objects so they can be sent as JSON strings
    serializer = SessionSerializer(linked_sessions, many=True)
    return Response({'result': serializer.data}, status=status.HTTP_200_OK)
