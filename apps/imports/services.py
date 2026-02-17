from __future__ import annotations

import os
import re
from datetime import date, datetime
from typing import Any, Dict, List, Tuple, Optional

from django.core.exceptions import ValidationError
from django.db import transaction

from openpyxl import load_workbook

from apps.clients.models import Client
from apps.imports.models import RawExcelRow, ImportBatch
from apps.imports.mapping import pick_any
from apps.imports.rules import EXACT, CONTAINS


# -------------------------
# базовые утилиты
# -------------------------

def _s(val: Any) -> str:
    if val is None:
        return ""
    return str(val).strip()


def normalize_header(text: Any) -> str:
    """
    Нормализация заголовков Excel:
    - lower
    - выкидываем emoji/пунктуацию (оставляем буквы/цифры)
    - схлопываем пробелы
    """
    if not text:
        return ""
    text = str(text).lower().strip()

    # заменяем всё "не буква/цифра" на пробел
    # (emoji тоже уйдут в пробел)
    text = re.sub(r"[^0-9a-zа-яё]+", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_phone(val: Any) -> str:
    """
    MVP-нормализация телефона:
    - если excel дал float -> "7999...0" или "... .0" — убираем
    - оставляем только цифры
    """
    raw = _s(val)
    if not raw:
        return ""

    raw = raw.replace(".0", "")
    digits = re.sub(r"\D+", "", raw)
    return digits


def normalize_date(val: Any) -> Optional[date]:
    """
    Возвращаем date или None.
    Поддержка:
    - date
    - datetime
    - строка вида "dd.mm.yyyy" / "yyyy-mm-dd"
    """
    if val is None:
        return None

    if isinstance(val, date) and not isinstance(val, datetime):
        return val

    if isinstance(val, datetime):
        return val.date()

    raw = _s(val)
    if not raw:
        return None

    raw = raw.replace(".0", "").strip()

    # dd.mm.yyyy
    m = re.match(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})$", raw)
    if m:
        d, mo, y = map(int, m.groups())
        return date(y, mo, d)

    # yyyy-mm-dd
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", raw)
    if m:
        y, mo, d = map(int, m.groups())
        return date(y, mo, d)

    return None


def normalize_cell_value(val: Any) -> Any:
    """
    Чтобы raw_data в JSONField не падал:
    - datetime/date -> isoformat
    - остальное как есть
    """
    if isinstance(val, datetime):
        return val.isoformat()
    if isinstance(val, date):
        return val.isoformat()
    return val


# -------------------------
# чтение файла
# -------------------------

def read_xlsx(file_path: str) -> Tuple[List[str], List[Tuple[int, Tuple[Any, ...]]]]:
    wb = load_workbook(file_path)
    sheet = wb.active

    headers = [_s(c.value) for c in sheet[1]]
    rows: List[Tuple[int, Tuple[Any, ...]]] = []

    for row_num, values in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
        rows.append((row_num, tuple(values)))

    return headers, rows


def row_to_dict(headers: List[str], values: Tuple[Any, ...]) -> Dict[str, Any]:
    """
    Делает dict:
    - ключи = нормализованные заголовки
    - значения = JSON-safe
    """
    data: Dict[str, Any] = {}
    for i, h in enumerate(headers):
        key = normalize_header(h)
        if not key:
            continue
        value = values[i] if i < len(values) else None
        data[key] = normalize_cell_value(value)
    return data


# -------------------------
# сборщики полей клиента
# -------------------------

def build_full_name(row_data: Dict[str, Any]) -> str:
    """
    ФИО: фамилия имя отчество (в правильном порядке)
    """
    last_name = _s(pick_any(row_data, exact=EXACT["last_name"]))
    first_name = _s(pick_any(row_data, exact=EXACT["first_name"]))
    middle_name = _s(pick_any(row_data, exact=EXACT["middle_name"]))

    parts = [p for p in [last_name, first_name, middle_name] if p]
    return " ".join(parts)


def build_address(row_data: Dict[str, Any]) -> str:
    """
    Адрес:
    1) Если есть длинная колонка доставки (contains) — берём её
    2) Иначе собираем из частей, если они есть
    """
    delivery = _s(pick_any(row_data, contains=CONTAINS["delivery_address_text"]))
    if delivery:
        return delivery


    idx = _s(pick_any(row_data, exact=EXACT.get("postal_index", [])))
    region = _s(pick_any(row_data, exact=EXACT.get("region", [])))
    city = _s(pick_any(row_data, exact=EXACT.get("city", [])))
    street = _s(pick_any(row_data, exact=EXACT.get("street", [])))
    house = _s(pick_any(row_data, exact=EXACT.get("house", [])))
    flat = _s(pick_any(row_data, exact=EXACT.get("flat", [])))

    parts = [p for p in [idx, region, city, street, house, flat] if p]
    return ", ".join(parts)


# -------------------------
# основной процессор
# -------------------------

class ExcelProcessor:
    @staticmethod
    @transaction.atomic
    def process_batch(batch: ImportBatch) -> dict:
        if not batch.file:
            raise ValidationError("Файл не загружен.")

        ext = os.path.splitext(batch.file.name)[1].lower()
        if ext != ".xlsx":
            raise ValidationError("Поддерживается только формат .xlsx (сохраните файл как .xlsx).")

        headers, rows = read_xlsx(batch.file.path)

        created_rows = 0
        created_clients = 0
        updated_clients = 0
        errors = 0


        RawExcelRow.objects.filter(batch=batch).delete()

        for row_num, values in rows:
            row_data = row_to_dict(headers, values)

            raw = RawExcelRow.objects.create(
                batch=batch,
                row_number=row_num,
                raw_data=row_data,
            )
            created_rows += 1


            phone = normalize_phone(pick_any(row_data, exact=EXACT["phone"]))
            if not phone:
                raw.error_message = "Пустой/некорректный телефон"
                raw.save(update_fields=["error_message"])
                errors += 1
                continue


            full_name = build_full_name(row_data) or phone
            email = _s(pick_any(row_data, exact=EXACT["email"]))
            contact = _s(pick_any(row_data, contains=CONTAINS["contact_text"]))
            pets = _s(pick_any(row_data, contains=CONTAINS["pets_text"]))
            address = build_address(row_data)

            dob_value = pick_any(row_data, exact=EXACT["dob"])
            dob = normalize_date(dob_value)


            defaults = {
                "name": full_name,
            }

            if hasattr(Client, "email"):
                defaults["email"] = email or ""
            if hasattr(Client, "address"):
                defaults["address"] = address or ""
            if hasattr(Client, "contact"):
                defaults["contact"] = contact or ""
            if hasattr(Client, "pets"):
                defaults["pets"] = pets or ""
            if hasattr(Client, "dob"):
                defaults["dob"] = dob  # date|None

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
            "rows": created_rows,
            "clients_created": created_clients,
            "clients_updated": updated_clients,
            "errors": errors,
        }
