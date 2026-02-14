from django.contrib import admin

from apps.orders.models import Order, OrderItem
from apps.stock.models import Product, StockItem


@admin.register(Product)
class Product(admin.ModelAdmin):
    list_display = ('name', 'type', 'variant', 'size')
    list_filter = ('type', 'variant')
    search_fields = ('name', 'type', 'variant')
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'sku', 'category', 'description')
        }),
        ('Цены и количество', {
            'fields': ('price', 'cost', 'quantity', 'min_quantity')
        }),
        ('Статус', {
            'fields': ('is_active', 'is_archived')
        }),
    )

@admin.register(StockItem)
class StockItem(admin.ModelAdmin):
    list_display = ('product', 'location', 'quantity',)
    list_filter = ('location',)
    search_fields = ('product', 'location', 'quantity',)


@admin.register(Order)
class Order(admin.ModelAdmin):
    list_display = ('client','event', 'status', 'assigned_packer', 'payment_status', 'registration_date')
    list_filter = ('client', 'event', 'status')
    inlines = [OrderItem]
    fieldsets = (
        ('Информация о заказе', {
            'fields': ('order_number', 'client', 'status', 'payment_status')
        }),
        ('Финансы', {
            'fields': ('subtotal', 'discount', 'total_amount')
        }),
        ('Доставка', {
            'fields': ('shipping_address', 'shipping_method', 'tracking_number')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at', 'paid_at')
        }),
    )
