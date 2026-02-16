from django.contrib import admin
from apps.orders.models import Order, OrderItem



class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    autocomplete_fields = ['product']

    def _has_full_access(self, request, obj=None):
        """True если пользователь имеет полный доступ"""
        return any([
            request.user.is_superuser,
            request.user.groups.filter(name='Owner').exists(),
            request.user.groups.filter(name='Admin').exists()
        ])

    def has_add_permission(self, request, obj=None):
        return self._has_full_access(request)

    def has_delete_permission(self, request, obj=None):
        return self._has_full_access(request)

    def has_change_permission(self, request, obj=None):
        return self._has_full_access(request)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('client', 'event', 'assigned_packer', 'status', 'payment_status', 'stock_location', 'created_at')
    list_filter = ('status','event', 'assigned_packer')
    search_fields = ('client__phone', 'client__name', 'event__name')
    inlines = [OrderItemInline]

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
        return qs.filter(assigned_packer=request.user)

    def has_add_permission(self, request):
        return self._has_full_access(request)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


    def has_change_permission(self, request, obj=None):

      if self._has_full_access(request):
          return True
      if obj is None:
          return True
      if obj.assigned_packer == request.user:
          return True

      return False



    def get_readonly_fields(self, request, obj=None):
        if self._has_full_access(request):
            return []
        else:
            return [field.name for field in self.model._meta.fields]

















