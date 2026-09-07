from django.contrib import admin
from apps.users.models import ClubMember


@admin.register(ClubMember)
class ClubMemberAdmin(admin.ModelAdmin):
    list_display = ('telegram_id', 'username', 'first_name', 'last_name', 'is_active')
    search_fields = ('telegram_id', 'username', 'first_name', 'last_name')
    list_filter = ('is_active',)


