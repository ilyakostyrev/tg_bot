from . import views
from django.urls import path
# Trainer URLs
urlpatterns = [
    # Trainer URLs
    # Trainer
    path('trainer/register/', views.register_trainer),
    path('trainer/generate_code/', views.generate_link_code_view),
    path('trainer/update_profile/', views.update_profile_trainer),
    path('trainer/add_free_time/', views.add_free_time),
    path('trainer/my_clients/<int:trainer_tg_id>/', views.get_trainer_clients),
    path('trainer/view_slots/', views.view_trainer_slots),
    path('trainer/delete_slot/<int:slot_id>/', views.delete_slot),

    # Client
    path('client/register/', views.register_client),
    path('client/update_profile/', views.update_profile_client),
    path('client/link_trainer/', views.link_client_to_trainer),
    path('client/log_weight/', views.log_weight),
    path('client/log_calories/', views.log_calories),
    path('client/available_slots/', views.get_available_slots),
    path('client/book_slot/', views.book_slot),
]