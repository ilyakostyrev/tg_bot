from django.db import models
from django.utils import timezone
# Если модель Trainer находится в другом приложении (например, bd_trainer), 
# раскомментируйте и поправьте следующую строку:
from bd_trainer.models import Trainer 

# Create your models here.
class Client(models.Model):
    tg_id = models.BigIntegerField(
        unique=True, 
        primary_key=True, 
        verbose_name="Telegram ID"
    )
    
    fullname = models.CharField(
        max_length=100, 
        null=True,         # <-- Добавлено: ФИО теперь необязательное поле
        blank=True,        # <-- Добавлено: ФИО теперь необязательное поле
        verbose_name="Полное имя"
    )

    username = models.CharField(
        max_length=50, 
        null=True, 
        blank=True, 
        verbose_name="Username Telegram"
    )
    email = models.EmailField(
        max_length=254, 
        null=True, 
        blank=True, 
        verbose_name="Email"
    )
    trainer = models.ForeignKey(
        Trainer, # Используем строку 'Trainer', чтобы избежать проблем с импортом, если модели находятся в разных файлах/приложениях
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='clients', 
        verbose_name="Тренер" # Добавил verbose_name для ясности
    )

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"

    def __str__(self):
        return f"{self.fullname or self.username} ({self.tg_id})"


class ProgressRecord(models.Model):
    """
    Модель для хранения ежедневных отчетов клиента (вес, калории).
    """
    client = models.ForeignKey(
        Client, 
        on_delete=models.CASCADE, 
        related_name='progress_records', 
        verbose_name="Клиент"
    )

    date = models.DateField(
        auto_now_add=True, 
        verbose_name="Дата записи"
    )
    
    weight = models.DecimalField(
        max_digits=5, 
        decimal_places=1,    
        null=True, 
        blank=True,    
        verbose_name="Вес"
    )
    
    calories_consumed = models.PositiveIntegerField(
        null=True, 
        blank=True,   
        verbose_name="Потреблено калорий"
    )

    class Meta:
        verbose_name = "Запись прогресса"
        verbose_name_plural = "Записи прогресса"
        # Гарантируем, что клиент может отправить только один отчет в день
        unique_together = ('client', 'date') 
        ordering = ['-date'] # Сортировка от новых записей к старым

    def __str__(self):
        return f"{self.client.fullname or self.client.username} - Отчет за {self.date.strftime('%Y-%m-%d')}"

