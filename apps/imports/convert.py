from __future__ import annotations

from pathlib import Path
import pandas as pd


def convert_xls_to_xlsx(src_path: str) -> str:
    src = Path(src_path)
    if src.suffix.lower() != ".xls":
        raise ValueError("convert_xls_to_xlsx ожидает .xls")

    dst = src.with_suffix(".xlsx")

    df = pd.read_excel(str(src), engine="xlrd")
    df.to_excel(str(dst), index=False, engine="openpyxl")

    return str(dst)
