from django.db import models



class Client(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=25, unique=True, db_index=True)
    dob = models.DateField(null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    contact = models.TextField(null=True, blank=True)
    pets = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name



