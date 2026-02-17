from django.contrib import admin
from django.contrib import messages
from apps.imports.models import ImportBatch, RawExcelRow

@admin.register(ImportBatch)
class ImportBatchAdmin(admin.ModelAdmin):
    list_display = ('event', 'uploaded_by', 'status', 'created_at')
    search_fields = ('file_name', 'uploaded_by__username', 'status')
    actions = ['process_batches']

    @admin.action(description="Process selected batches")
    def process_batches(self, request, queryset):
        processed_count = 0
        errors = []

        for batch in queryset:
            try:
                batch.process()   # <-- ВАЖНО
                processed_count += 1
            except Exception as e:
                errors.append(f"{getattr(batch, 'file_name', batch.pk)} - {e}")

        if processed_count:
            self.message_user(
                request,
                f"Successfully processed {processed_count} batches.",
                level=messages.SUCCESS
            )

        if errors:
            self.message_user(
                request,
                "Errors:\n" + "\n".join(errors[:10]),
                level=messages.ERROR
            )

        if not processed_count and not errors:
            self.message_user(
                request,
                "No batches were processed.",
                level=messages.WARNING
            )



@admin.register(RawExcelRow)
class RawExcelRowAdmin(admin.ModelAdmin):
    list_display = ('batch', 'row_number', 'error_message')
    list_filter = ('batch', 'error_message')
    search_fields = ('batch__file_name', 'linked_client__phone')




