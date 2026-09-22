import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from datetime import datetime
from apps.parser.services.event_writer import save_event
import re


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
    date_element = soup.select_one(".event-page__date")

    start_date, end_date = parse_event_dates(
        date_element.get_text(" ", strip=True)
    )
    activities = []

    for card in soup.select(".race-card"):

        activity = parse_race_card(card)

        if activity["distance"] is None:
            continue

        activities.append(activity)

    return {
        "source": "regplace",
        "external_id": parse_event_external_id(event_card["url"]),
        "name": title.get_text(" ", strip=True),
        "city": event_card["city"],
        "date": start_date,
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
        "sport": meta_parts[-1] if len(meta_parts) > 1 else "",
    }



def fetch_running_events():
    return [
        event
        for event in fetch_all_events()
        if is_running_event(event)
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
        if distance is None:
            distance = parse_distance_from_name(name)
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


def is_running_event(event):
    sports = [
        sport.strip()
        for sport in event["sport"].split(",")
    ]

    return "Бег" in sports


def parse_event_dates(value):
    if not value:
        return None, None

    if "–" not in value:
        start_date = datetime.strptime(
            value,
            "%d.%m.%Y",
        ).date()

        return start_date, None

    start_value, end_value = value.split("–", 1)

    end_date = datetime.strptime(
        end_value,
        "%d.%m.%Y",
    ).date()

    start_date = datetime.strptime(
        f"{start_value}.{end_date.year}",
        "%d.%m.%Y",
    ).date()

    return start_date, end_date


def parse_distance_from_name(name):

    if not name:
        return None

    match = re.search(
        r"(\d+(?:[.,]\d+)?)\s*(км|м)\.?(?:\s|$)",
        name.lower(),
    )

    if not match:
        return None

    value = float(
        match.group(1).replace(",", ".")
    )

    unit = match.group(2)

    if unit == "м":
        return value / 1000

    return value


def import_events():
    event_cards = fetch_running_events()
    imported = []

    for event_card in event_cards:
        html = fetch_event_page(event_card["url"])
        clean_event = parse_event_page(event_card, html)

        event = save_event(clean_event)
        imported.append(event)

    return imported