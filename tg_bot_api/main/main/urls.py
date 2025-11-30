from django.urls import path, include

urlpatterns = [
    path('api/', include("bd_trainer.urls")),
    path('api/', include("bd_client.urls")),
]
# ImportError: cannot import name 'Сlient' from 'bd_client.models' (C:\Users\User\Desktop\tg_bot\tg_bot\main\bd_client\models.py) что за ошибка? 