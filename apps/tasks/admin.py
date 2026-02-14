from django.contrib import admin

from apps.tasks.models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'assignee', 'status')
    list_filter = ('assignee', 'status')
    search_fields = ('title', 'status', 'description',)
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'category')
        }),
        ('Назначение', {
            'fields': ('assigned_to', 'created_by')
        }),
        ('Статус и приоритет', {
            'fields': ('status', 'priority')
        }),
        ('Даты', {
            'fields': ('due_date', 'completed_at')
        }),
    )

