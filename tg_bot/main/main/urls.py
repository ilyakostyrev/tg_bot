from bd_trainer import views
from django.urls import path

urlpatterns = [
    # Trainer URLs
    path('trainer/api/', views.trainer_create, name = 'trainer_create'),
    path('trainer/api/<int:tg_id>/', views.trainer_update, name = 'trainer_update'),# td_id
    path('trainer/api/<int:tg_id>/delete/', views.trainer_delete, name = 'trainer_delete'),# td_id
    path('trainer/api/<int:tg_id>/', views.trainer_detail, name = 'trainer_detail'),# td_id
    path('trainer/api/list/', views.trainer_list, name = 'trainer_list'),
    # AvailableSlot URLs
    path('available_slot/api/', views.available_slot_create, name = 'available_slot_create'),
    path('available_slot/api/<int:slot_id>/', views.available_slot_update, name = 'available_slot_update'),# slot_id
    path('available_slot/api/<int:slot_id>/delete/', views.available_slot_delete, name = 'available_slot_delete'),# slot_id
    path('available_slot/api/<int:slot_id>/', views.available_slot_detail, name = 'available_slot_detail'),# slot_id
    path('available_slot/api/list/', views.available_slot_list, name = 'available_slot_list'),
]
