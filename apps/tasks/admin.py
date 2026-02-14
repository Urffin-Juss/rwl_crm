from django.contrib import admin

from apps.tasks.models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'assigned', 'status')
    list_filter = ('assigned', 'status')
    search_fields = ('title', 'status', 'description',)


