from django.db import models

class ClubMember(models.Model):
    telegram_id = models.IntegerField(unique=True, blank=False, null=False)
    username = models.CharField(unique=True, max_length=100, blank=True, null=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(unique=False, max_length=100, blank=True, null=True)
    photo_url = models.URLField(unique=False, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username or f'{self.first_name} {self.last_name}'.strip()