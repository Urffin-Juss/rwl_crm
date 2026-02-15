from django.contrib import admin

from apps.tasks.models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'assigned', 'status')
    list_filter = ('assigned', 'status')
    search_fields = ('title', 'status', 'description',)


    def get_queryset(self, request):
        qs = super().get_queryset(request)


        if request.user.is_superuser:
            return qs


        full_access_groups = ['Owner','Аdmin']
        if request.user.groups.filter(name__in=full_access_groups).exists():
            return qs


        return qs.filter(assigned=request.user)


