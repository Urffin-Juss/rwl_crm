from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Tuple


from django.core.exceptions import ValidationError, FieldDoesNotExist
from django.db import transaction
from openpyxl import load_workbook

from apps.clients.models import Client
from apps.imports.models import RawExcelRow, ImportBatch
from apps.imports.rules import EXACT, CONTAINS


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

        return {
            "rows_saved": created_rows,
            "clients_created": created_clients,
            "clients_updated": updated_clients,
            "errors": errors,
            "skipped_empty_rows": skipped_empty,
        }
