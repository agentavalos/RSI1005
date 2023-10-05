from django.urls import path
from .views import index, calculate_accuracy


urlpatterns = [
    path('', index),
    path("calculate_accuracy", calculate_accuracy, name="calculate_accuracy")
]
