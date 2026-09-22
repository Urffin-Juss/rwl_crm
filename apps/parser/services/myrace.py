import requests
from bs4 import BeautifulSoup

BASE_URL = "https://myrace.info"


def fetch_events_page():
    response = requests.get(
        f"{BASE_URL}/events",
        timeout=30,
    )
    response.raise_for_status()
    return response.text


def parse_event_card(card):
    href = card.get("href")

    name_element = card.select_one("h2")
    date_element = card.select_one(".date")
    city_element = card.select_one(".flag")
    type_element = card.select_one(".type")

    return {
        "external_id": href.rstrip("/").split("/")[-1],
        "url": href,
        "name": name_element.get_text(" ", strip=True),
        "date": date_element.get_text(" ", strip=True),
        "city": city_element.get_text(" ", strip=True),
        "sport": type_element.get_text(" ", strip=True),
    }