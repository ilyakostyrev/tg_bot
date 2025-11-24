from bd_trainer import views
from django.urls import path
# Trainer URLs
urlpatterns = [
    # Trainer URLs
    path('trainer/create/',views.trainer_create, name = 'trainer_create'),
    path('trainer/<int:tg_id>/update/', views.trainer_update, name = 'trainer_update'),# td_id
    path('trainer/<int:tg_id>/delete/', views.trainer_delete, name = 'trainer_delete'),# td_id
    path('trainer/<int:tg_id>/detail/', views.trainer_detail, name = 'trainer_detail'),# td_id
    path('trainer/list/', views.trainer_list, name = 'trainer_list'),
    # AvailableSlot URLs
    path('trainer/available_slot/create/', views.available_slot_create, name = 'available_slot_create'),
    path('trainer/available_slot/<int:slot_id>/update/', views.available_slot_update, name = 'available_slot_update'),# slot_id
    path('trainer/available_slot/<int:slot_id>/delete/', views.available_slot_delete, name = 'available_slot_delete'),# slot_id
    path('trainer/available_slot/<int:slot_id>/', views.available_slot_detail, name = 'available_slot_detail'),# slot_id
    path('trainer/available_slot/list/', views.available_slot_list, name = 'available_slot_list'),
]