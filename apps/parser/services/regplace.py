import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from datetime import datetime



BASE_URL = "https://reg.place"


def fetch_events_page(page_url="/events"):

    response = requests.get(

        f"{BASE_URL}{page_url}",

        timeout=30,

    )

    response.raise_for_status()

    return response.text


def fetch_event_page(event_url):

    response = requests.get(

        f"{BASE_URL}{event_url}",

        timeout=30,

    )

    response.raise_for_status()

    return response.text


def parse_event_page(event_card, html):
    soup = BeautifulSoup(html, "html.parser")

    title = soup.select_one(".event-page__title")
    date = soup.select_one(".event-page__date")

    activities = [
        parse_race_card(card)
        for card in soup.select(".race-card")
    ]

    return {
        "source": "regplace",
        "external_id": parse_event_external_id(event_card["url"]),
        "name": title.get_text(" ", strip=True),
        "city": event_card["city"],
        "date": parse_event_date(date.get_text(" ", strip=True)),
        "activities": activities,
    }


def parse_event_card(card):
    title_link = card.select_one(".b-event-card__title-link")
    meta = card.select_one(".b-event-card__meta")

    meta_parts = [
        text
        for text in meta.stripped_strings
        if text != "•"
    ]

    return {
        "name": title_link.get_text(strip=True),
        "url": title_link.get("href"),
        "date": meta_parts[0],
        "city": meta_parts[1] if len(meta_parts) == 3 else "",
        "sport": meta_parts[-1],
    }



def fetch_running_events():
    events = fetch_events()

    return [
        event
        for event in events
        if event["sport"] == "Бег"
    ]


def fetch_events():
    html = fetch_events_page()
    soup = BeautifulSoup(html, "html.parser")

    cards = soup.select("article.b-event-card")

    return [
        parse_event_card(card)
        for card in cards
    ]



def parse_race_card(card):
    title = card.select_one(".race-card__title")

    name = title.get_text(" ", strip=True)
    distance = None

    for item in card.select(".race-card__meta-item"):
        label = item.select_one(".race-card__meta-label")

        if label and label.get_text(strip=True) == "Дистанция":
            values = list(item.stripped_strings)
            distance = parse_distance(values[-1])
            break

    return {
        "external_id": build_activity_external_id(name, distance),
        "name": name,
        "distance": distance,
    }


def parse_distance(value):

    if not value:

        return None

    value = value.strip().lower().replace(",", ".")

    if value.endswith("км"):

        return float(value.removesuffix("км").strip())

    if value.endswith("м"):

        meters = float(value.removesuffix("м").strip())

        return meters / 1000

    return None


def parse_event_external_id(event_url):

    path = urlparse(event_url).path

    return path.rstrip("/").split("/")[-1]


def parse_event_date(value):
    if not value:
        return None

    return datetime.strptime(value, "%d.%m.%Y").date()


def build_activity_external_id(name, distance):
    return f"{name}:{distance}"



def fetch_all_events():
    events = []
    page_url = "/events"

    while page_url:
        html = fetch_events_page(page_url)
        soup = BeautifulSoup(html, "html.parser")

        cards = soup.select("article.b-event-card")

        for card in cards:
            events.append(parse_event_card(card))

        next_link = soup.select_one('a[rel="next"]')

        if next_link:
            page_url = next_link.get("href")
        else:
            page_url = None

    return events