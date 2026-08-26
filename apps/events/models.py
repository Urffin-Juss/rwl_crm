from django.db import models
from django.db.models.fields import CharField, DecimalField


class Event(models.Model):

    STATUS_CHOICES = (
    ('OPEN', 'OPEN'),
    ('CLOSED', 'CLOSED'),
    )

    name = models.CharField(max_length=200, verbose_name="Название")
    city = models.CharField(max_length=200, verbose_name="Город")
    date = models.DateField(verbose_name="Дата")
    status = models.CharField(choices=STATUS_CHOICES, max_length=200, default='OPEN', verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлен")


    def __str__(self):
        return self.name

    class Meta:
        db_table = 'event'
        ordering = ['-date']
        verbose_name = "Ивент"
        verbose_name_plural = "Ивенты"



class EventDistance(models.Model):
    event = models.ForeignKey(Event, related_name='distances', on_delete=models.CASCADE)
    name = models.CharField(max_length=50, blank=False)
    distance = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.event} — {self.name} ({self.distance} км)'

    class Meta:
        verbose_name = "Дистанция"
        verbose_name_plural = "Дистанции"

