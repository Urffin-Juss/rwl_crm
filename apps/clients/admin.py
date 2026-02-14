from django.contrib import admin

from apps.clients.models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'created_at', 'dob')
    search_fields = ('name', 'phone')
    list_filter = ('city', 'created_at')


