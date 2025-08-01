from django.urls import path

from .views import api_create_resource

urlpatterns = [
    path('api/resources/', api_create_resource),
]