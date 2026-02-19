from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.clients.models import Client
from apps.events.models import Event
from apps.orders.models import Order, OrderItem
from apps.stock.models import Product, StockItem, StockLocation


class OrderItemModelTests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(name="Race", city="Moscow", date=date(2026, 1, 1))
        self.client_obj = Client.objects.create(name="Client", phone="79990000111")
        self.product = Product.objects.create(type="SOCKS", name="Socks")

    def test_create_deducts_stock_on_regular_location(self):
        location = StockLocation.objects.create(name="Main_stock", location="Main")
        StockItem.objects.create(product=self.product, location=location, quantity=5)
        order = Order.objects.create(client=self.client_obj, event=self.event, stock_location=location)

        OrderItem.objects.create(order=order, product=self.product, quantity=2, price=0)

        stock = StockItem.objects.get(product=self.product, location=location)
        self.assertEqual(stock.quantity, 3)

    def test_delete_returns_stock_on_regular_location(self):
        location = StockLocation.objects.create(name="Main_stock", location="Main")
        StockItem.objects.create(product=self.product, location=location, quantity=5)
        order = Order.objects.create(client=self.client_obj, event=self.event, stock_location=location)

        item = OrderItem.objects.create(order=order, product=self.product, quantity=2, price=0)
        item.delete()

        stock = StockItem.objects.get(product=self.product, location=location)
        self.assertEqual(stock.quantity, 5)

    def test_updating_quantity_is_forbidden(self):
        location = StockLocation.objects.create(name="Main_stock", location="Main")
        StockItem.objects.create(product=self.product, location=location, quantity=5)
        order = Order.objects.create(client=self.client_obj, event=self.event, stock_location=location)

        item = OrderItem.objects.create(order=order, product=self.product, quantity=1, price=0)
        item.quantity = 2
        with self.assertRaises(ValidationError):
            item.save()

    def test_tech_stock_bypasses_quantity_check(self):
        location = StockLocation.objects.create(name="Tech_stock", location="Tech")
        order = Order.objects.create(client=self.client_obj, event=self.event, stock_location=location)

        item = OrderItem.objects.create(order=order, product=self.product, quantity=99, price=0)
        self.assertIsNotNone(item.pk)
