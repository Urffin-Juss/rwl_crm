from django.db import models


class Event(models.Model):

    STATUS_CHOICES = (
    ('OPEN', 'OPEN'),
    ('CLOSED', 'CLOSED'),
    )

    name = models.CharField(max_length=200)
    city = models.CharField(max_length=200)
    date = models.DateField()
    status = models.CharField(choices=STATUS_CHOICES, max_length=200, default='OPEN')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.name

    class Meta:
        db_table = 'event'
        ordering = ['-date']




