from __future__ import annotations
from pathlib import Path
import pandas as pd


def convert_xls_ro_xlsx(src_path: str) -> str:
        """
        Конвертирует .xls -> .xlsx
        Возвращает путь до нового .xlsx
        """

        src = Path(src_path)
        if src.suffix.lower() != ".xls":
            raise ValueError("converter waiting for .xls")


        dst = src.with_suffix(".xlsx")


        df = pd.read_exel(src_path, engine="xlrd")
        df.to_excel(dst, index=False, engine="openpyxl")


        return str(dst)