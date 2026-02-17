# apps/imports/services.py

from __future__ import annotations

from dataclasses import dataclass
import os
import re
from typing import Any, Dict, List, Tuple

from django.core.exceptions import ValidationError
from django.db import transaction

from openpyxl import load_workbook

from apps.clients.models import Client
from apps.imports.models import RawExcelRow, ImportBatch



COL_PHONE = "Мобильный телефон"
COL_EMAIL = "Электронная почта"
COL_LAST_NAME = "Фамилия"
COL_FIRST_NAME = "Имя"
COL_PATRONYMIC = "Отчество"
COL_DOB = "Дата рождения"


ADDR_COLS = [
    "Почтовый индекс",
    "Регион",
    "Населенный пункт",
    "Улица",
    "Дом",
    "Квартира",
]


def _s(val: Any) -> str:
    """Безопасно привести к строке и обрезать пробелы."""
    if val is None:
        return ""
    return str(val).strip()


def normalize_phone(val: Any) -> str:
    """
    MVP-нормализация телефона:
    - убираем пробелы/скобки/дефисы
    - если пришло как число с .0 — убираем .0
    """
    raw = _s(val)
    if not raw:
        return ""


    raw = raw.replace(".0", "")


    digits = re.sub(r"\D+", "", raw)
    return digits


def build_full_name(row: Dict[str, Any]) -> str:
    parts = [
        _s(row.get(COL_LAST_NAME)),
        _s(row.get(COL_FIRST_NAME)),
        _s(row.get(COL_PATRONYMIC)),
    ]
    return " ".join([p for p in parts if p])


def build_address(row: Dict[str, Any]) -> str:
    parts = []
    for col in ADDR_COLS:
        v = _s(row.get(col))
        if v:
            parts.append(v)
    return ", ".join(parts)


def read_xlsx(file_path: str) -> Tuple[List[str], List[Tuple[int, Tuple[Any, ...]]]]:
    wb = load_workbook(file_path)
    sheet = wb.active

    headers = [ _s(c.value) for c in sheet[1] ]
    rows: List[Tuple[int, Tuple[Any, ...]]] = []

    for row_num, values in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
        rows.append((row_num, tuple(values)))

    return headers, rows


def row_to_dict(headers: List[str], values: Tuple[Any, ...]) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    for i, h in enumerate(headers):
        if not h:
            continue
        data[h] = values[i] if i < len(values) else None
    return data


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


        if COL_PHONE not in headers:
            raise ValidationError(f"В файле нет обязательной колонки: '{COL_PHONE}'.")

        created_rows = 0
        created_clients = 0
        updated_clients = 0
        errors = 0


        RawExcelRow.objects.filter(batch=batch).delete()

        for row_num, values in rows:
            data = row_to_dict(headers, values)

            raw = RawExcelRow.objects.create(
                batch=batch,
                row_number=row_num,
                raw_data=data,
            )
            created_rows += 1

            phone = normalize_phone(data.get(COL_PHONE))
            if not phone:
                raw.error_message = "Пустой/некорректный телефон"
                raw.save(update_fields=["error_message"])
                errors += 1
                continue

            full_name = build_full_name(data) or phone
            email = _s(data.get(COL_EMAIL))
            address = build_address(data)


            defaults = {
                "name": full_name,
            }
            if hasattr(Client, "email"):
                defaults["email"] = email
            if hasattr(Client, "address"):
                defaults["address"] = address
            if hasattr(Client, "birth_date"):
                defaults["birth_date"] = data.get(COL_DOB)

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
