from django.db import models

# Create your models here.
class Client(models.Model):
 tg_id = models.BigIntegerField( unique=True,  primary_key=True,  verbose_name="Telegram ID" )
    
 fullname = models.CharField( max_length=100,  verbose_name="Полное имя" )

 username = models.CharField(   max_length=50,  null=True, blank=True,  verbose_name="Username Telegram" )
 email = models.EmailField( max_length=254,   null=True, blank=True,  verbose_name="Email" )

class ProgressRecord(models.Model):
    """
    Модель для хранения ежедневных отчетов клиента (вес, калории).
    """
    client = models.ForeignKey(  Client,   on_delete=models.CASCADE,   related_name='progress_records', verbose_name="Клиент" )

    date = models.DateField(  auto_now_add=True,  verbose_name="Дата записи" )
    
    weight = models.DecimalField( max_digits=5, decimal_places=1,    null=True, blank=True,    verbose_name="Вес" )
    
    calories_consumed = models.PositiveIntegerField(   null=True, blank=True,   verbose_name="Потреблено калорий"   )

    class Meta:
        verbose_name = "Запись прогресса"
        verbose_name_plural = "Записи прогресса"
        # Гарантируем, что клиент может отправить только один отчет в день
        unique_together = ('client', 'date') 
        ordering = ['-date'] # Сортировка от новых записей к старым

    def __str__(self):
        return f"{self.client.fullname} - Отчет за {self.date.strftime('%Y-%m-%d')}"