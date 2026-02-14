from django.contrib import admin

from apps.orders.models import Order, OrderItem


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('client', 'event', 'assigned_packer', 'status', 'payment_status')
    list_filter = ('status','event', 'assigned_packer')
    search_fields = ('client_phone', 'client_name', 'status')
    inlines = [OrderItem]
