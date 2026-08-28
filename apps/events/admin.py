from django.contrib import admin

from apps.events.models import Event, EventParticipation, EventDistance


class EventDistanceInline(admin.TabularInline):
    model = EventDistance
    extra = 8


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'date', 'status')
    list_filter = ('city', 'status')
    search_fields = ('name', 'city', 'status')
    date_hierarchy = 'date'

    inlines = [EventDistanceInline]


@admin.register(EventParticipation)
class EventParticipationAdmin(admin.ModelAdmin):
    list_display = ('event', 'distance', 'date')
    list_filter = ('event', 'distance', 'date')
    search_fields = ('event', 'distance', 'date')
    date_hierarchy = 'date'








