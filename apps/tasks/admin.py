from django.contrib import admin

from apps.tasks.models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'assigned', 'status')
    list_filter = ('assigned', 'status')
    search_fields = ('title', 'status', 'description',)

    def _has_full_access(self, request):
        """True если пользователь имеет полный доступ"""
        return any([
            request.user.is_superuser,
            request.user.groups.filter(name='Owner').exists(),
            request.user.groups.filter(name='Admin').exists()
        ])

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if self._has_full_access(request):
            return qs
        return qs.filter(assigned=request.user)

    def has_add_permission(self, request):
        return self._has_full_access(request)

    def has_delete_permission(self, request, obj=None):
        return self._has_full_access(request)

    def has_change_permission(self, request, obj=None):

        if self._has_full_access(request):
            return True
        if hasattr(obj, 'assigned') and obj.assigned == request.user:
            return True

        return False


