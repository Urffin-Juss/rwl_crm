from django.contrib import admin

from apps.clients.models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'created_at',)
    search_fields = ('name', 'phone')
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'client_group', 'status')
        }),
        ('Контакты', {
            'fields': ('email', 'phone', 'address')
        }),
        ('Дополнительно', {
            'fields': ('notes', 'birth_date', 'is_active')
        }),
    )


