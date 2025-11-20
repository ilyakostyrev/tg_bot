from django.db import models

# Create your models here.
# 
class Trainer(models.Model):
 tg_id = models.BigIntegerField( unique=True,  primary_key=True,  verbose_name="Telegram ID" )
    
 fullname = models.CharField( max_length=100,  verbose_name="Полное имя" )

 username = models.CharField(   max_length=50,  null=True, blank=True,  verbose_name="Username Telegram" )
 email = models.EmailField( max_length=254,   null=True, blank=True,  verbose_name="Email" )

def __str__(self):
        return f"{self.fullname} (@{self.username or 'N/A'})"

class AvailableSlot(models.Model):
    trainer = models.ForeignKey( Trainer,  on_delete=models.CASCADE,   related_name='available_slots', )

    start_time = models.DateTimeField(verbose_name="Время начала")
    
    end_time = models.DateTimeField(verbose_name="Время окончания")

    is_booked = models.BooleanField(default=False, verbose_name="Забронирован")
    class Meta:
         unique_together = ('trainer', 'start_time') 
         
    def __str__(self):
        status = "Занят" if self.is_booked else "Свободен"
        # Форматируем вывод времени в читабельный вид
        return f"{self.trainer.fullname} | {self.start_time.strftime('%d.%m %H:%M')} - {self.end_time.strftime('%H:%M')} [{status}]"

    