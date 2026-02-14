from django.contrib import admin

from apps.orders.models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('client', 'event', 'assigned_packer', 'status', 'payment_status')
    list_filter = ('status','event', 'assigned_packer')
    search_fields = ('client__phone', 'client__name', 'event__name')
    inlines = [OrderItemInline]





