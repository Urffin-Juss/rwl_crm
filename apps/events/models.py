from django.db import models


class Event(models.Model):
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=200)
    date = models.DateField()
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.name

    class Meta:
        db_table = 'event'
        ordering = ['-date']



# Create your models here.
