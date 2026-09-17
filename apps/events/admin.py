from django.contrib import admin

from apps.events.models import Event, EventParticipation, EventActivity


class EventActivityInline(admin.TabularInline):
    model = EventActivity
    extra = 8


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'date', 'status')
    list_filter = ('city', 'status')
    search_fields = ('name', 'city', 'status')
    date_hierarchy = 'date'

    inlines = [EventActivityInline]


@admin.register(EventParticipation)
class EventParticipationAdmin(admin.ModelAdmin):
    list_display = (
        'member',
        'event',
        'distance',
        'status',
        'looking_for_company',
        'created_at',
    )
    list_filter = (
        'status',
        'looking_for_company',
        'event',
    )
    search_fields = (
        'member__username',
        'member__first_name',
        'member__last_name',
        'event__name',
    )








