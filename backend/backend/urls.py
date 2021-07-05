"""backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from UserSECA.views import GetAuthToken

urlpatterns = [
    # api endpoints related to Users app
    path('api/UserSECA/', include('UserSECA.urls')),

    # api endpoints related to SECAAlgo app
    path('api/SECAAlgo/', include('SECAAlgo.urls')),

    # api endpoints related to Wiki
    path('api/Wiki/', include('Wiki_SECA.urls')),

    # api endpoints related to authentication
    path('auth/', GetAuthToken.as_view(), name="auth"),

    # misc endpoints
    path('admin/', admin.site.urls),

    # expert questions endpoints
    path('api/Expert/', include('expert_questions_SECA.urls')),
]
