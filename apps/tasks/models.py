from django.db import models

from config import settings


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

    title = models.CharField(max_length=100)
    type = models.CharField(max_length=100, choices=TYPE_CHOICES, default='EVENT')
    event = models.ForeignKey('events.Event', on_delete=models.CASCADE, null=True, blank=True)
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, null=True, blank=True)
    assigned= models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=100, choices=STATUS_CHOICES, default='TODO')
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return str(self.assigned)


