from django.contrib import admin, messages
from django.db import transaction
from django.contrib import admin
from apps.imports.services import ExcelProcessor
from apps.imports.models import ImportBatch, RawExcelRow

@admin.register(ImportBatch)
class ImportBatchAdmin(admin.ModelAdmin):
    list_display = ("event", "uploaded_by", "status", "created_at")
    search_fields = ("file_name", "uploaded_by__username", "status")
    actions = ["process_batches"]

    @admin.action(description="Process selected batches")
    def process_batches(self, request, queryset):
        self.status = self.STATUS_PROCESSING
        self.save(update_fields=["status"])
        process_import_batch_task.delay(self.id)


        processed = 0
        failed = 0

        for batch in queryset:
            try:
                # лучше в try, чтобы один плохой файл не валил остальные
                with transaction.atomic():
                    ExcelProcessor.process_batch(batch)
                    batch.status = "DONE"
                    batch.save(update_fields=["status"])
                processed += 1
            except Exception as e:
                batch.status = "FAILED"
                batch.save(update_fields=["status"])
                failed += 1
                self.message_user(
                    request,
                    f"{batch.file_name}: {e}",
                    level=messages.ERROR
                )

        if processed:
            self.message_user(
                request,
                f"Processed: {processed}, failed: {failed}",
                level=messages.SUCCESS if failed == 0 else messages.WARNING
            )


@admin.register(RawExcelRow)
class RawExcelRowAdmin(admin.ModelAdmin):
    list_display = ('batch', 'row_number', 'error_message')
    list_filter = ('batch', 'error_message')
    search_fields = ('batch__file_name', 'linked_client__phone')




