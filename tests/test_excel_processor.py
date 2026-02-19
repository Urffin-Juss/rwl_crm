import os
import tempfile
from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from openpyxl import Workbook

from apps.clients.models import Client
from apps.events.models import Event
from apps.imports.models import ImportBatch, RawExcelRow
from apps.imports.services import ExcelProcessor
from apps.orders.models import Order, OrderItem
from apps.stock.models import Product, StockItem, StockLocation

User = get_user_model()


H_LAST = "\u0424\u0430\u043c\u0438\u043b\u0438\u044f"
H_FIRST = "\u0418\u043c\u044f"
H_MIDDLE = "\u041e\u0442\u0447\u0435\u0441\u0442\u0432\u043e"
H_DOB = "\u0414\u0430\u0442\u0430 \u0440\u043e\u0436\u0434\u0435\u043d\u0438\u044f"
H_PHONE = "\u041c\u043e\u0431\u0438\u043b\u044c\u043d\u044b\u0439 \u0442\u0435\u043b\u0435\u0444\u043e\u043d"
H_EMAIL = "\u042d\u043b\u0435\u043a\u0442\u0440\u043e\u043d\u043d\u0430\u044f \u043f\u043e\u0447\u0442\u0430"
H_CITY = "\u0413\u043e\u0440\u043e\u0434"
H_STREET = "\u0423\u043b\u0438\u0446\u0430"
H_HOUSE = "\u0414\u043e\u043c"
H_FLAT = "\u041a\u0432\u0430\u0440\u0442\u0438\u0440\u0430"
H_DISTANCE = "\u0414\u0438\u0441\u0442\u0430\u043d\u0446\u0438\u044f"
H_PRODUCT = "\u0411\u0415\u0413\u041e\u0412\u042b\u0415 \u041d\u041e\u0421\u041a\u0418, \u0440\u0430\u0437\u043c\u0435\u0440 41-45, \u0446\u0432\u0435\u0442 \u0447\u0435\u0440\u043d\u044b\u0439"


def make_xlsx(path: str, headers: list[str], rows: list[list]):
    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append(row)
    wb.save(path)


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
class ExcelProcessorTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u1", password="123")
        self.event = Event.objects.create(name="Sadovoe", city="Moscow", date=date(2026, 1, 1))

        self.batch = ImportBatch.objects.create(
            event=self.event,
            uploaded_by=self.user,
            file_name="test.xlsx",
            file_hash="hash123",
            status="PROCESSING",
            file=SimpleUploadedFile(
                "placeholder.xlsx",
                b"placeholder",
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
        )

        self.tech_stock = StockLocation.objects.create(name="Tech_stock", location="Tech")

    def _attach_file_path_to_batch(self, file_path: str):
        with open(file_path, "rb") as src:
            self.batch.file.save(os.path.basename(file_path), File(src), save=True)
        self.batch.file_name = os.path.basename(file_path)
        self.batch.save(update_fields=["file_name"])

    def test_process_batch_creates_clients_orders_rows(self):
        headers = [
            H_LAST,
            H_FIRST,
            H_MIDDLE,
            H_DOB,
            H_PHONE,
            H_EMAIL,
            H_CITY,
            H_STREET,
            H_HOUSE,
            H_FLAT,
            H_DISTANCE,
            H_PRODUCT,
        ]

        rows = [["Ivanov", "Ivan", "Ivanovich", date(1990, 1, 1), "+7 (916) 123-45-67", "ivan@test.ru", "Moscow", "Tverskaya", "1", "10", "5km", 2]]

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
        self.assertTrue(client.phone)
        self.assertIn("Ivan", client.name)

        order = Order.objects.first()
        self.assertEqual(order.event, self.event)
        self.assertTrue(timezone.is_aware(order.registration_date))

        if hasattr(order, "stock_location"):
            self.assertEqual(order.stock_location.name, "Tech_stock")

        self.assertIn("rows_saved", result)
        self.assertIn("errors", result)

    def test_process_batch_skips_empty_rows(self):
        headers = [H_PHONE, H_FIRST, H_LAST]
        rows = [[None, None, None], ["", "", ""], ["+7 999 111-22-33", "Petr", "Petrov"]]

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
        regular_stock = StockLocation.objects.create(name="Main_stock", location="Main")
        order = Order.objects.create(client=client, event=self.event, stock_location=regular_stock)
        product = Product.objects.create(type="SOCKS", name="Socks")
        StockItem.objects.create(product=product, location=regular_stock, quantity=0)

        with self.assertRaises(ValidationError):
            OrderItem.objects.create(order=order, product=product, quantity=1, price=0)
