import re
from typing import Any, Dict, Iterable, Optional


def norm_headers(s: str) -> Iterable[str]:

    s = (s or "").strip().lower()
    s = s.replace("\n", " ")
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\s+$", " ", s)
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^0-9a-zа-яё ]+", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s+", " ", s).strip()

    return s

def pick_exact(row: Dict[str, Any], header: str) -> Any:

    return row.get(header)

def pick_contains(row: Dict[str, Any], header: str) -> Any:

    n = norm_headers(needle)
    for k, v in row.items():
        if n in norm_headers(k):
            return v
    return None


def pick_any(row: Dict[str, Any], *, exact: Optional[str]=None, contains: Optional[str]=None) -> Any:

    if exact:
        val = pick_exact(row, exact)
        if val not in [None, ""]:
            return val
        if contains:
            return pick_contains(row, contains)
    return None