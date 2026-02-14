from django.contrib import admin

from apps.events.models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'date', 'status')
    list_filter = ('city', 'status')
    search_fields = ('name', 'city', 'status')
    date_hierarchy = 'date'





