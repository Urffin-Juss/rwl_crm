from django.db import models
from config import settings
from django.db.models import JSONField


class ImportBatch(models.Model):

    STATUS_CHOICES = [
        ('NEW', 'New'),
        ('PROCESSING', 'Processing'),
        ('DONE', 'Done'),
        ('FAILED', 'Failed'),
    ]


    event = models.ForeignKey('events.Event', on_delete=models.CASCADE)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=255)
    file_hash = models.CharField(max_length=255)
    status = models.CharField(max_length=255, choices=STATUS_CHOICES, default='New')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    file = models.FileField(upload_to='imports/')
    processed_at = models.DateTimeField(null=True, blank=True)
    result = models.JSONField(null=True, blank=True, default=dict)
    error = models.TextField(blank=True, default="")


    def __str__(self):
        return str(self.event)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['event', 'file_hash'],
                name='unique_event_file_hash'
            )
        ]

    def process(self):
        from apps.imports.services import ExcelProcessor
        return ExcelProcessor.process_batch(self)


class RawExcelRow(models.Model):
    batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE)
    row_number = models.IntegerField()
    raw_data = models.JSONField()
    linked_client = models.ForeignKey('clients.Client', on_delete=models.SET_NULL, null=True)
    linked_order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True)
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
