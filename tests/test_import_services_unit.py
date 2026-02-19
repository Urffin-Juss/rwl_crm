from datetime import date

from django.test import TestCase

from apps.imports.services import (
    build_order_items,
    make_product_title,
    normalize_date,
    normalize_header,
    normalize_phone,
    parse_product_column,
)


class ImportServicesUnitTests(TestCase):
    def test_normalize_phone_handles_common_formats(self):
        self.assertEqual(normalize_phone("+7 (916) 123-45-67"), "79161234567")
        self.assertEqual(normalize_phone("8 916 123 45 67"), "79161234567")
        self.assertEqual(normalize_phone("9161234567"), "79161234567")
        self.assertEqual(normalize_phone("abc"), "")

    def test_normalize_date_supports_multiple_formats(self):
        self.assertEqual(normalize_date(date(2026, 2, 19)), "2026-02-19")
        self.assertEqual(normalize_date("2026-02-19"), "2026-02-19")
        self.assertEqual(normalize_date("19.02.2026"), "2026-02-19")
        self.assertEqual(normalize_date("2026-02-19T00:00:00"), "2026-02-19")

    def test_parse_product_column_and_title(self):
        header = "\u0411\u0415\u0413\u041e\u0412\u042b\u0415 \u041d\u041e\u0421\u041a\u0418"
        parsed = parse_product_column(header, 2)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["type"], "socks")
        self.assertEqual(parsed["quantity"], 2)

        title = make_product_title(parsed)
        self.assertTrue(title)

    def test_build_order_items_picks_product_like_columns(self):
        row = {
            normalize_header("\u0411\u0415\u0413\u041e\u0412\u042b\u0415 \u041d\u041e\u0421\u041a\u0418"): 1,
            normalize_header("\u0418\u043c\u044f"): "Ivan",
        }
        items = build_order_items(row)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["quantity"], 1)
