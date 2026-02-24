from django.db import models


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




