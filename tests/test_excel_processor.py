import os
import tempfile
from datetime import date

from django.test import TestCase, override_settings
from django.core.exceptions import ValidationError

from openpyxl import Workbook

from apps.imports.services import ExcelProcessor
from apps.imports.models import ImportBatch, RawExcelRow
from apps.clients.models import Client
from apps.events.models import Event
from apps.stock.models import StockLocation, StockItem, Product
from apps.orders.models import Order, OrderItem
from django.contrib.auth import get_user_model


User = get_user_model()


def make_xlsx(path: str, headers: list[str], rows: list[list]):
    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for r in rows:
        ws.append(r)
    wb.save(path)


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
class ExcelProcessorTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u1", password="123")
        self.event = Event.objects.create(name="Sadovoe")  # подстрой под свои поля Event

        self.batch = ImportBatch.objects.create(
            event=self.event,
            uploaded_by=self.user,
            file_name="test.xlsx",
            file_hash="hash123",  # если у тебя unique — делай уникальным
            status="PROCESSING",
        )

        # “тех” склад
        self.tech_stock = StockLocation.objects.create(name="Tech_stock", location="Tech")



    def test_process_batch_creates_clients_orders_rows(self):
        headers = [
            "Фамилия", "Имя", "Отчество", "Дата рождения",
            "Мобильный телефон", "Электронная почта",
            "Город", "Улица", "Дом", "Квартира",
            "Дистанция",
            "БЕГОВЫЕ НОСКИ, размер 41-45, цвет черный⚫",
        ]

        rows = [
            ["Иванов", "Иван", "Иванович", date(1990, 1, 1),
             "+7 (916) 123-45-67", "ivan@test.ru",
             "г Москва", "Тверская", "1", "10",
             "5км", 2],
        ]

        fd, xlsx_path = tempfile.mkstemp(suffix=".xlsx")
        os.close(fd)
        make_xlsx(xlsx_path, headers, rows)
        self._attach_file_path_to_batch(xlsx_path)


        product = Product.objects.create(type="SOCKS", name="test socks", variant="black", size="41-45")
        StockItem.objects.create(product=product, location=self.tech_stock, quantity=10)



        result = ExcelProcessor.process_batch(self.batch)

        self.assertEqual(RawExcelRow.objects.filter(batch=self.batch).count(), 1)
        self.assertEqual(Client.objects.count(), 1)
        self.assertEqual(Order.objects.count(), 1)

        client = Client.objects.first()
        self.assertTrue(client.phone)      # телефон нормализован
        self.assertIn("Иван", client.name) # имя собралось

        order = Order.objects.first()
        self.assertEqual(order.event, self.event)


        if hasattr(order, "stock_location"):
            self.assertEqual(order.stock_location.name, "Tech_stock")

        # result dict (как у тебя в конце)
        self.assertIn("rows_saved", result)
        self.assertIn("errors", result)

    def test_process_batch_skips_empty_rows(self):
        headers = ["Мобильный телефон", "Имя", "Фамилия"]
        rows = [
            [None, None, None],
            ["", "", ""],
            ["+7 999 111-22-33", "Петр", "Петров"],
        ]

        fd, xlsx_path = tempfile.mkstemp(suffix=".xlsx")
        os.close(fd)
        make_xlsx(xlsx_path, headers, rows)
        self._attach_file_path_to_batch(xlsx_path)

        result = ExcelProcessor.process_batch(self.batch)


        self.assertEqual(RawExcelRow.objects.filter(batch=self.batch).count(), 1)
        self.assertEqual(Client.objects.count(), 1)
        self.assertEqual(result["errors"], 0)

    def test_orderitem_requires_stock_location(self):

        client = Client.objects.create(name="A", phone="79990000000")
        order = Order.objects.create(client=client, event=self.event)

        product = Product.objects.create(type="SOCKS", name="Socks")

        with self.assertRaises(ValidationError):
            OrderItem.objects.create(order=order, product=product, quantity=1, price=0)

    def test_orderitem_requires_stock_quantity(self):

        client = Client.objects.create(name="A", phone="79990000000")
        order = Order.objects.create(client=client, event=self.event, stock_location=self.tech_stock)
        product = Product.objects.create(type="SOCKS", name="Socks")

        StockItem.objects.create(product=product, location=self.tech_stock, quantity=0)

        with self.assertRaises(ValidationError):
            OrderItem.objects.create(order=order, product=product, quantity=1, price=0)
