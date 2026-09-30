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



def extract_settlement_from_address(address: str) -> str:
    if not address:
        return ""

    matches = re.findall(
        r"(?<!\w)(?:село|деревня|аул|рп)\s+([^,]+)",
        address,
        flags=re.IGNORECASE,
    )

    if not matches:
        return ""

    return matches[-1].strip()


def normalize_settlement(address: str) -> str:
    city = extract_city_from_address(address)

    if city:
        return city

    return extract_settlement_from_address(address)