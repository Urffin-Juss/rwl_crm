from django.db import models

from django.conf import settings



class Task(models.Model):

    TYPE_CHOICES = [
        ('EVENT', 'Event'),
        ('ORDER', 'Order'),
    ]
    STATUS_CHOICES = [
        ('TODO', 'toDo'),
        ('DOING', 'Doing'),
        ('DONE', 'Done'),
    ]

    title = models.CharField(max_length=100, verbose_name='Название')
    type = models.CharField(max_length=100, choices=TYPE_CHOICES, default='EVENT', verbose_name='Тип задачи')
    event = models.ForeignKey('events.Event', on_delete=models.CASCADE, null=True, blank=True, verbose_name='Ивент')
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, null=True, blank=True, verbose_name='Заказ')
    assigned= models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Исполнитель')
    status = models.CharField(max_length=100, choices=STATUS_CHOICES, default='TODO', verbose_name='Статус')
    description = models.TextField(null=True, blank=True, verbose_name='Описание')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создана')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлена')


    def __str__(self):
        return str(self.assigned)

    class Meta:
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"


class ArchiveTask(Task):
    class Meta:
        proxy = True
        verbose_name = "Архивная задача"
        verbose_name_plural = "Архивные задачи"

