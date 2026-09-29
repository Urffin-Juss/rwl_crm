import re


def extract_city_from_address(address: str) -> str:
    if not address:
        return ""

    matches = re.findall(
        r"(?<!\w)г(?:\.\s*|\s+)([^,]+)",
        address,
        flags=re.IGNORECASE,
    )

    if not matches:
        return ""

    return matches[-1].strip()