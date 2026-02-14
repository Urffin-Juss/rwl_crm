from django.contrib import admin

from apps.events.models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'date', 'status')
    list_filter = ('city', 'status')
    search_fields = ('name', 'city', 'status')
    date_hierarchy = 'start_date'
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'event_type', 'description', 'status')
        }),
        ('Даты и место', {
            'fields': ('start_date', 'end_date', 'location')
        }),
        ('Дополнительно', {
            'fields': ('max_participants', 'price', 'image')
        }),
    )




