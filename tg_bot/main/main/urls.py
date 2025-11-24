from django.urls import path, include

urlpatterns = [
    path('api/', include('bd_trainer.urls')),
]
