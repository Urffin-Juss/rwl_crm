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

    actions = ('move_to_archive', 'restore_from_archive')

    inlines = [EventActivityInline]

    @admin.action(description='Перевести выбранные ивенты в архив')
    def move_to_archive(self, request, queryset):
        queryset.update(status='CLOSED')

    @admin.action(description='Вернуть выбранные ивенты из архива')
    def restore_from_archive(self, request, queryset):
        queryset.update(status='OPEN')


@admin.register(EventParticipation)
class EventParticipationAdmin(admin.ModelAdmin):
    list_display = (
        'member',
        'event',
        'activity',
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









