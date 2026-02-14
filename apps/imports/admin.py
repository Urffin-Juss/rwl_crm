from django.contrib import admin

@admin.register(Import)
class ImportBatchAdmin(admin.ModelAdmin):
    list_display = ('event', 'uploaded_by', 'status', 'created_at')
    search_fields = ('name', 'notes')
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'import_type', 'description')
        }),
        ('Статус', {
            'fields': ('status', 'error_message')
        }),
        ('Файлы', {
            'fields': ('source_file',)
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at', 'completed_at')
        }),
        ('Автор', {
            'fields': ('created_by',)
        }),
    )
class RawExcelRowAdmin(admin.ModelAdmin):
    list_display = ('batch', 'row_number', 'error_message')
    search_fields = ('linked_client', 'batch', 'row_number')

