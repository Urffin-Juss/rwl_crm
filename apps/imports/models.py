from django.db import models

from apps.events.models import Event
from config import settings


class ImportBatch(models.Model):

    STATUS_CHOICES = [
        ('PROCESSING', 'Processing'),
        ('DONE', 'Done'),
        ('FAILED', 'Failed'),
    ]


    event = models.ForeignKey('events.Event', on_delete=models.CASCADE)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=255)
    file_hash = models.CharField(max_length=255)
    status = models.CharField(max_length=255, choices=STATUS_CHOICES, default='PROCESSING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return str(self.event)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['event', 'file_hash'],
                name='unique_event_file_hash'
            )
        ]


class RawExcelRow(models.Model):
    batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE)
    row_number = models.IntegerField()
    raw_data = models.JSONField()
    linked_client = models.ForeignKey('clients.Client', on_delete=models.CASCADE, null=True)
    linked_order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, null=True)
    error_message = models.TextField(null=True, blank=True)

    def __str__(self):
        return str(self.batch)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['batch', 'row_number'],
                name='unique_row_per_import'
            )
        ]
