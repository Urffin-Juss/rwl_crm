import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.reg.place"


def fetch_events_page():

    response = requests.get(

        f"{BASE_URL}/events",

        timeout=30,

    )

    response.raise_for_status()

    return response.text


def parse_event_card(card):
    title_link = card.select_one(".b-event-card__title-link")
    meta = card.select_one(".b-event-card__meta")

    return {
        "name": title_link.get_text(strip=True),
        "url": title_link.get("href"),
        "meta": meta.get_text(" ", strip=True),
    }


def fetch_first_event():
    html = fetch_events_page()
    soup = BeautifulSoup(html, "html.parser")

    card = soup.select_one("article.b-event-card")

    if card is None:
        return None

    return parse_event_card(card)


