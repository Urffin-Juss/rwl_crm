from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Tuple, Optional

from django.core.exceptions import ValidationError
from django.db import transaction
from openpyxl import load_workbook

from apps.clients.models import Client
from apps.imports.models import RawExcelRow, ImportBatch
from apps.imports.rules import EXACT, CONTAINS  # оставим твой подход


def _s(val: Any) -> str:
    if val is None:
        return ""
    return str(val).strip()


def normalize_header(text: Any) -> str:
    # приводим заголовки к “сравнимому” виду
    t = _s(text).lower()
    t = re.sub(r"\s+", " ", t)
    return t


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


def pick_any(row: Dict[str, Any], *, exact: Optional[List[str]] = None, contains: Optional[List[str]] = None) -> Any:
    """
    exact: список “точных” названий колонок (как в rules.py), но сравнение нормализованное
    contains: список подстрок (тоже нормализованных)
    """
    exact = exact or []
    contains = contains or []

    exact_norm = [normalize_header(x) for x in exact]
    contains_norm = [normalize_header(x) for x in contains]

    for key, value in row.items():
        k = normalize_header(key)

        if k in exact_norm:
            return value

        if any(part and part in k for part in contains_norm):
            return value

    return None


def normalize_phone(val: Any) -> str:
    raw = _s(val)
    if not raw:
        return ""

    raw = raw.replace(".0", "")  # если прилетело как 7916...0
    digits = re.sub(r"\D+", "", raw)

    # MVP-валидация: РФ обычно 11 цифр (7XXXXXXXXXX)
    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]

    if len(digits) < 10:
        return ""

    return digits


def build_full_name(row: Dict[str, Any]) -> str:
    last_name = _s(pick_any(row, exact=EXACT["last_name"]))
    first_name = _s(pick_any(row, exact=EXACT["first_name"]))
    middle_name = _s(pick_any(row, exact=EXACT["middle_name"]))

    parts = [p for p in [last_name, first_name, middle_name] if p]
    return " ".join(parts)


def build_address(row: Dict[str, Any]) -> str:
    # можно собрать из “Регион/Город/Улица/Дом/Квартира”, если они есть
    region = _s(pick_any(row, exact=EXACT.get("region", [])))
    city = _s(pick_any(row, exact=EXACT.get("city", [])))
    street = _s(pick_any(row, exact=EXACT.get("street", [])))
    house = _s(pick_any(row, exact=EXACT.get("house", [])))
    flat = _s(pick_any(row, exact=EXACT.get("flat", [])))

    parts = [p for p in [region, city, street, house, flat] if p]
    return ", ".join(parts)


class ExcelProcessor:
    @staticmethod
    @transaction.atomic
    def process_batch(batch: ImportBatch) -> dict:
        if not batch.file:
            raise ValidationError("Файл не загружен.")

        ext = os.path.splitext(batch.file.name)[1].lower()
        if ext != ".xlsx":
            raise ValidationError("Поддерживается только .xlsx (сохраните файл как .xlsx).")

        headers, rows = read_xlsx(batch.file.path)

        # чистим строки этого батча (клиентов НЕ трогаем)
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

            full_name = build_full_name(data) or phone
            email = _s(pick_any(data, exact=EXACT["email"]))
            address = build_address(data)  # или pick_any(... contains=...) если надо

            defaults = {"name": full_name}
            if hasattr(Client, "email"):
                defaults["email"] = email
            if hasattr(Client, "address"):
                defaults["address"] = address

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
