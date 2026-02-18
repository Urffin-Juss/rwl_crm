from __future__ import annotations

from datetime import datetime

from apps.imports.utils import get_tech_stock_location
from apps.orders.models import OrderItem, Order
from apps.stock.models import Product
import os
import re
from typing import Any, Dict, List, Tuple, Optional

from django.core.exceptions import ValidationError, FieldDoesNotExist
from django.db import transaction
from openpyxl import load_workbook

from apps.clients.models import Client
from apps.imports.models import RawExcelRow, ImportBatch
from apps.imports.rules import EXACT, CONTAINS, PRODUCT_KEYWORDS


def _s(val: Any) -> str:
    if val is None:
        return ""
    return str(val).strip()


def normalize_header(text: str) -> str:
    if not text:
        return ""
    text = str(text).lower().strip()

    text = re.sub(r"[^0-9a-zа-яё]+", " ", text, flags=re.IGNORECASE)

    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_cell_value(val: Any) -> Any:
    """
    Делает значение безопасным для JSONField.
    datetime/date -> ISO строка
    остальное -> как есть (str/int/float/bool/None)
    """
    if val is None:
        return None
    # openpyxl может отдавать datetime/date
    try:
        import datetime as _dt
        if isinstance(val, (_dt.datetime, _dt.date)):
            return val.isoformat()
    except Exception:
        pass
    return val


def read_xlsx(file_path: str) -> Tuple[List[str], List[Tuple[int, Tuple[Any, ...]]]]:
    wb = load_workbook(file_path)
    sheet = wb.active

    headers = [_s(c.value) for c in sheet[1]]
    rows: List[Tuple[int, Tuple[Any, ...]]] = []

    for row_num, values in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
        rows.append((row_num, tuple(values)))

    return headers, rows


def row_to_dict(headers: List[str], values: Tuple[Any, ...]) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    for i, h in enumerate(headers):
        key = normalize_header(h)
        if not key:
            continue
        v = values[i] if i < len(values) else None
        data[key] = normalize_cell_value(v)
    return data


def pick_any(row: dict, exact=None, contains=None):
    exact = [normalize_header(x) for x in (exact or [])]
    contains = [normalize_header(x) for x in (contains or [])]

    for key, value in row.items():
        normalized = normalize_header(key)

        if normalized in exact:
            return value

        if any(c in normalized for c in contains):
            return value

    return None

def model_has_field(model, field_name: str) -> bool:
    try:
        model._meta.get_field(field_name)
        return True
    except FieldDoesNotExist:
        return False

def _is_empty_row(values) -> bool:
    def _empty(v):
        if v is None:
            return True
        if isinstance(v, str) and not v.strip():
            return True
        return False
    return all(_empty(v) for v in values)

def normalize_phone(val: Any) -> str:

    raw = _s(val)
    if not raw:
        return ""

    # Excel-числа типа 79161234567.0
    if raw.endswith(".0"):
        raw = raw[:-2]

    digits = re.sub(r"\D+", "", raw)


    if len(digits) == 10:
        digits = "7" + digits


    if len(digits) == 11 and digits[0] in ("7", "8"):
        if digits[0] == "8":
            digits = "7" + digits[1:]
        return digits

    return ""


def normalize_date(val: Any) -> str:
    """
    Преобразует дату в YYYY-MM-DD
    Принимает: datetime, date, ISO строку, строку DD.MM.YYYY
    """
    if val is None:
        return ""

    # Если это datetime/date объект
    if hasattr(val, 'strftime'):
        return val.strftime('%Y-%m-%d')

    raw = _s(val)
    if not raw:
        return ""

    # Если это ISO строка с временем (1996-05-27T00:00:00)
    if 'T' in raw:
        return raw.split('T')[0]


    if re.match(r'^\d{4}-\d{2}-\d{2}$', raw):
        return raw


    match = re.search(r'^(\d{1,2})\.(\d{1,2})\.(\d{4})$', raw.strip())
    if match:
        day, month, year = match.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"

    return ""




def build_full_name(row: Dict[str, Any]) -> str:
    last_name = _s(pick_any(row, exact=EXACT["last_name"]))
    first_name = _s(pick_any(row, exact=EXACT["first_name"]))
    middle_name = _s(pick_any(row, exact=EXACT["middle_name"]))

    parts = [p for p in [last_name, first_name, middle_name] if p]
    return " ".join(parts)


def build_notes(row: Dict[str, Any]) -> str:
    """Собирает все дополнительные поля в одну строку для notes"""
    parts = []

    # Профессия
    profession = _s(pick_any(row, exact=EXACT["profession"]))
    if profession:
        parts.append(f"Профессия: {profession}")

    # Клуб
    club = _s(pick_any(row, exact=EXACT["club"]))
    if club:
        parts.append(f"Клуб: {club}")



    return " | ".join(parts)


def build_address(row: Dict[str, Any]) -> str:
    """Собирает полный адрес из составных частей"""
    parts = []


    city = _s(pick_any(row, exact=EXACT["city"]))
    if city:
        parts.append(f"г. {city}")


    street = _s(pick_any(row, exact=EXACT["street"]))
    if street:
        parts.append(f"ул. {street}")

    # Дом
    house = _s(pick_any(row, exact=EXACT["house"]))
    if house:
        parts.append(f"д. {house}")

    # Квартира
    flat = _s(pick_any(row, exact=EXACT["flat"]))
    if flat:
        parts.append(f"кв. {flat}")

    # Если есть готовый адрес (например, из поля "Укажите адрес для доставки")
    full_address = _s(pick_any(row, contains=CONTAINS.get("delivery_address_text", [])))
    if full_address and not parts:  # используем только если нет составных частей
        return full_address

    return ", ".join(parts)

def is_empty_row(values) -> bool:
    """
    Проверяем, полностью ли строка пустая.
    Пустая = все ячейки None или пустые строки.
    """
    for v in values:
        if v is None:
            continue
        if str(v).strip() != "":
            return False
    return True




def parse_product_column(header: str, value: Any) -> Optional[Dict]:
    """
    Парсит колонку с товаром.
    Возвращает словарь с типом товара, размером, цветом и количеством
    """
    if not value or str(value).strip() == "":
        return None

    header_lower = header.lower()
    value_str = str(value).strip()

    # Определяем тип товара
    product_type = None
    for ptype, keywords in PRODUCT_KEYWORDS.items():
        if any(kw in header_lower for kw in keywords):
            product_type = ptype
            break

    if not product_type:
        return None

    result = {
        'type': product_type,
        'name': header[:200],  # обрезаем длинное название
        'size': None,
        'color': None,
        'quantity': 1  # по умолчанию 1, если не указано иное
    }

    # Пытаемся извлечь размер
    size_match = re.search(r'размер\s+([\d\-SML\/]+)', header_lower, re.IGNORECASE)
    if size_match:
        result['size'] = size_match.group(1)

    # Пытаемся извлечь цвет
    color_match = re.search(r'цвет\s+([а-яё]+)', header_lower, re.IGNORECASE)
    if color_match:
        result['color'] = color_match.group(1)

    # Если значение - число, это может быть количество
    if value_str.isdigit() and int(value_str) > 0:
        result['quantity'] = int(value_str)

    return result

def make_product_title(p: dict) -> str:
    """
    p: {type, size, color, name, quantity}
    """
    t = p.get("type")

    if t == "socks":
        base = "Носки беговые"
    elif t == "headband":
        base = "Повязка спортивная"
    elif t == "belt":
        base = "Пояс для соревнований"
    elif t == "mug":
        base = "Кружка"
    elif t == "donation":
        base = "Донат в приют"
    elif t == "insurance":
        base = "Страховка"
    elif t == "sticker":
        base = "Наклейка"
    else:
        base = "Товар"

    parts = [base]

    size = p.get("size")
    color = p.get("color")

    if size:
        parts.append(str(size))
    if color:
        parts.append(str(color))

    return ", ".join(parts)[:200]



def build_order_items(row: Dict[str, Any]) -> List[Dict]:
    """
    Собирает все товары из строки Excel
    """
    items = []

    for header, value in row.items():
        # Проверяем, похоже ли на товарную колонку
        if any(kw in header.lower() for kw in ['носок', 'носки', 'повязк', 'пояс', 'кружк', 'донат']):
            product_data = parse_product_column(header, value)
            if product_data:
                items.append(product_data)

    return items


def get_or_create_product(product_data: Dict) -> Product:
    """
    Находит или создает товар по данным из Excel
    """
    # Формируем название товара
    name_parts = [product_data['name']]
    if product_data.get('size'):
        name_parts.append(f"размер {product_data['size']}")
    if product_data.get('color'):
        name_parts.append(f"цвет {product_data['color']}")

    product_name = make_product_title(product_data)

    # Пытаемся найти существующий
    product, created = Product.objects.get_or_create(
        name=product_name,
        defaults={
            'type': product_data['type'],
            'variant': product_data.get('color', ''),
            'size': product_data.get('size', ''),
        }
    )

    return product



class ExcelProcessor:
    @staticmethod
    @transaction.atomic
    def process_batch(batch: ImportBatch) -> dict:
        headers = []
        rows = []


        for row_num, values in rows:
            data = row_to_dict(headers, values)

            raw = RawExcelRow.objects.create(
                batch=batch,
                row_number=row_num,
                raw_data=data,
            )



        if not batch.file:
            raise ValidationError("Файл не загружен.")

        ext = os.path.splitext(batch.file.name)[1].lower()
        if ext != ".xlsx":
            raise ValidationError("Поддерживается только .xlsx (сохраните файл как .xlsx).")

        headers, rows = read_xlsx(batch.file.path)


        RawExcelRow.objects.filter(batch=batch).delete()

        created_rows = 0
        created_clients = 0
        updated_clients = 0
        errors = 0
        skipped_empty = 0

        for row_num, values in rows:
            # 1) пропускаем реально пустые строки
            if not any(v is not None and _s(v) != "" for v in values):
                skipped_empty += 1
                continue

            data = row_to_dict(headers, values)

            raw = RawExcelRow.objects.create(
                batch=batch,
                row_number=row_num,
                raw_data=data,
            )
            created_rows += 1

            phone = normalize_phone(pick_any(data, exact=EXACT["phone"]))
            if not phone:
                raw.error_message = "Пустой/некорректный телефон"
                raw.save(update_fields=["error_message"])
                errors += 1
                continue

            city = _s(pick_any(data, exact=EXACT["city"]))
            contact = _s(pick_any(data, contains=CONTAINS["contact_text"]))
            pets = _s(pick_any(data, contains=CONTAINS["pets_text"]))
            email = _s(pick_any(data, exact=EXACT["email"]))
            address = build_address(data)
            full_name = build_full_name(data)
            notes = build_notes(data)



            dob = normalize_date(pick_any(data, exact=EXACT["dob"]))

            defaults = {
                "name": full_name,
                "email": email,
                "city": city,
                "address": address,  # ← исправленный адрес
                "contact": contact,
                "pets": pets,
                "notes": notes,  # ← новые заметки
                "dob": dob or None,
            }

            if model_has_field(Client, "email"):
                defaults["email"] = email

            if model_has_field(Client, "city"):
                defaults["city"] = city

            if model_has_field(Client, "address"):
                defaults["address"] = address

            if model_has_field(Client, "contact"):
                defaults["contact"] = contact

            if model_has_field(Client, "pets"):
                defaults["pets"] = pets

            if model_has_field(Client, "dob"):
                defaults["dob"] = dob or None

            if model_has_field(Client, "notes"):
                defaults["notes"] = notes or None

            client, created = Client.objects.update_or_create(
                phone=phone,
                defaults=defaults,
            )

            raw.linked_client = client
            raw.save(update_fields=["linked_client"])

            if created:
                created_clients += 1
            else:
                updated_clients += 1


            tech_loc = get_tech_stock_location()
            distance = _s(pick_any(data, exact=EXACT["distance"]))
            bib = _s(pick_any(data, exact=EXACT["bib_number"]))
            chip = _s(pick_any(data, exact=EXACT["chip_number"]))
            product = make_product_title(data)


            order = Order.objects.create(
                client=client,
                event=batch.event,
                distance_text=distance,
                status='new',
                payment_status='NOT_PAID',
                payment_type='cash',
                registration_date=datetime.now().date(),
                comments=f"Номер: {bib}, Чип: {chip}".strip(", "),
                stock_location=tech_loc,

            )


            items_data = build_order_items(data)
            for item_data in items_data:
                product = get_or_create_product(item_data)

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item_data['quantity'],
                    price=0,
                )


            raw.linked_client = client
            raw.linked_order = order
            raw.save(update_fields=["linked_client", "linked_order"])

            if created:
                created_clients += 1
            else:
                updated_clients += 1


        return {
            "rows_saved": created_rows,
            "clients_created": created_clients,
            "clients_updated": updated_clients,
            "orders_created": created_rows - errors,
            "errors": errors,
            "skipped_empty_rows": skipped_empty,
        }
