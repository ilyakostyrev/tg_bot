from django.db import models

# Create your models here.
# 
class Trainer(models.Model):
 tg_id = models.BigIntegerField( unique=True,  primary_key=True,  verbose_name="Telegram ID" )
    
 fullname = models.CharField( max_length=100,  verbose_name="Полное имя" )

 username = models.CharField(   max_length=50,  null=True, blank=True,  verbose_name="Username Telegram" )
 email = models.EmailField( max_length=254,   null=True, blank=True,  verbose_name="Email" )
 link_code = models.CharField(max_length=10, unique=True, null=True, blank=True, verbose_name="Код ссылки")

def __str__(self):
        return f"{self.fullname} (@{self.username or 'N/A'})"

class AvailableSlot(models.Model):
    trainer = models.ForeignKey(
        Trainer,  
        on_delete=models.CASCADE,   
        related_name='available_slots',
        verbose_name="Тренер"
    )

    start_time = models.DateTimeField(verbose_name="Время начала")
    
    duration_minutes = models.PositiveIntegerField(verbose_name="Продолжительность (минуты)", default=60)

    is_booked = models.BooleanField(default=False, verbose_name="Забронирован")
    
    class Meta:
         unique_together = ('trainer', 'start_time') 
         verbose_name = "Доступный слот"
         verbose_name_plural = "Доступные слоты"
         
    def __str__(self):
        status = "Занят" if self.is_booked else "Свободен"
        return f"{self.trainer.fullname or self.trainer.username} | {self.start_time.strftime('%d.%m %H:%M')} ({self.duration_minutes} мин.) [{status}]"
