from django.urls import path, include
from rest_framework import routers
from .views import UserViewSet, get_sessions_from_user

router = routers.DefaultRouter()
router.register('users', UserViewSet)

urlpatterns = [path('', include(router.urls)),
               path('get_sessions', get_sessions_from_user, name="get_sessions")]


