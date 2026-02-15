from django.contrib import admin
from apps.stock.models import Product, StockItem, StockLocation


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'variant', 'size')
    list_filter = ('type', 'variant')
    search_fields = ('name', 'type', 'variant')


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'location',)
    list_filter = ('location',)
    search_fields = ('product_name', 'location_name',)


@admin.register(StockLocation)
class StockLocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'created_at')
    list_filter = ('location', 'name')


