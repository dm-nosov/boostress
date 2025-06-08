from django.urls import path

from .views import home, api_create_order

urlpatterns = [
    path('', home),
    path('api/orders/', api_create_order),
]