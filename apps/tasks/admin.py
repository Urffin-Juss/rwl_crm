from django.contrib import admin

from apps.tasks.models import Task, ArchiveTask
from apps.webui.templatetags.dashboard_tags import register


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
        if obj is None:
            return True
        if obj.assigned == request.user:
            return True

        return False

    def get_readonly_fields(self, request, obj=None):
        if self._has_full_access(request):
            return []
        else:
            return [field.name for field in self.model._meta.fields]


@admin.register(ArchiveTask)
class ArchiveTaskAdmin(admin.ModelAdmin):
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
        qs = qs.filter(status="completed")

        if self._has_full_access(request):
            return qs

        return qs.filter(assigned_packer=request.user)


