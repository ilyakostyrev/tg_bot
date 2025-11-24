from bd_trainer import views
from django.urls import path

urlpatterns = [
    path('trainer/api/', views.trainer_create, name = 'trainer_create'),
    path('trainer/api/<int:tg_id>/', views.trainer_update, name = 'trainer_update'),# td_id
    path('trainer/api/<int:tg_id>/delete/', views.trainer_delete, name = 'trainer_delete'),# td_id
    path('trainer/api/<int:tg_id>/', views.trainer_detail, name = 'trainer_detail'),# td_id
    path('trainer/api/list/', views.trainer_list, name = 'trainer_list'),
]
