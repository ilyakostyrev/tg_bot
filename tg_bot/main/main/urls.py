from bd_trainer import views
from django.urls import path

urlpatterns = [
    path('trainer/api/', views.trainer_create, name = 'trainer_create'),
]
