from . import views
from django.urls import path
# Trainer URLs
urlpatterns = [
    path('client/progress/report/', views.client_progress_report, name='client_progress_report'),
    path('client/progress/<int:tg_id>/', views.get_client_progress, name='get_client_progress'),
    path('client/progress/summary/<int:tg_id>/<int:year>/<int:month>/', views.get_monthly_progress_summary, name='get_monthly_progress_summary'),
    path('client/progress/delete/<int:tg_id>/<str:date_str>/', views.delete_progress_record, name='delete_progress_record'),
    path('client/list/', views.list_clients, name='list_clients'),
    path('client/register/', views.register_client, name='register_client'),

    path('client/link_trainer/', views.client_link_trainer, name='client-link-trainer'),
    path('client/update_profile/', views.client_update_profile, name='client-update-profile'),
]