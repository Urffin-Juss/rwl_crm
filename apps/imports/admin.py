from django.contrib import admin
from apps.imports.services import ExcelProcessor
from apps.imports.models import ImportBatch, RawExcelRow

@admin.register(ImportBatch)
class ImportBatchAdmin(admin.ModelAdmin):
    list_display = ('event', 'uploaded_by', 'status', 'created_at')
    search_fields = ('file_name', 'uploaded_by__username', 'status')
    actions = ['process_batches']

    @admin.action(description="Process selected batches")
    def process_batch(self):
        result = ExcelProcessor.process_batch(self)
        self.status = "DONE"
        self.save(update_fields=["status"])
        return result



@admin.register(RawExcelRow)
class RawExcelRowAdmin(admin.ModelAdmin):
    list_display = ('batch', 'row_number', 'error_message')
    list_filter = ('batch', 'error_message')
    search_fields = ('batch__file_name', 'linked_client__phone')




