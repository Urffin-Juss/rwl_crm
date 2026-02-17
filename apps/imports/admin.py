from django.contrib import admin

from apps.imports import models
from apps.imports.models import ImportBatch, RawExcelRow


@admin.register(ImportBatch)
class ImportBatchAdmin(admin.ModelAdmin):
    list_display = ('event', 'uploaded_by', 'status', 'created_at')
    search_fields = ('file_name', 'uploaded_by', 'status')
    file = models.FileField(upload_to='imports/', null=True, blank=True)


@admin.register(RawExcelRow)
class RawExcelRowAdmin(admin.ModelAdmin):
    list_display = ('batch', 'row_number', 'error_message')
    list_filter = ('batch', 'error_message')
    search_fields = ('batch__file_name', 'linked_client__phone')




