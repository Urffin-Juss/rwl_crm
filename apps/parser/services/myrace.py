import requests
from bs4 import BeautifulSoup
import re
from datetime import date
from apps.parser.services.event_writer import save_event





BASE_URL = "https://myrace.info"


RUNNING_SPORTS = {
    "Бег",
    "Трейл",
    "Скайраннинг",
}


MONTHS = {
    "января": 1,
    "февраля": 2,
    "марта": 3,
    "апреля": 4,
    "мая": 5,
    "июня": 6,
    "июля": 7,
    "августа": 8,
    "сентября": 9,
    "октября": 10,
    "ноября": 11,
    "декабря": 12,
}


def parse_event_dates(value, year):
    if not value or not year:
        return None, None

    parts = value.lower().split()

    if len(parts) == 2:
        day = int(parts[0])
        month = MONTHS[parts[1]]

        return date(year, month, day), None

    if len(parts) == 4 and parts[1] == "-":
        start_day = int(parts[0])
        end_day = int(parts[2])
        month = MONTHS[parts[3]]

        return (
            date(year, month, start_day),
            date(year, month, end_day),
        )

    return None, None


def parse_event_date(soup):
    header = soup.select_one(".event-header")

    if header is None:
        return None, None

    date_link = header.select_one('a[href^="/take/"]')

    if date_link is None:
        return None, None

    value = date_link.get_text(" ", strip=True)
    href = date_link.get("href", "")

    match = re.fullmatch(r"/take/(\d{4})", href)

    if match is None:
        return None, None

    year = int(match.group(1))

    return parse_event_dates(value, year)

def fetch_event_page(event_url):

    response = requests.get(
        f"{BASE_URL}{event_url}",
        timeout=30,
    )
    response.raise_for_status()
    return response.text

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

    registration_status = name_element.select_one(".registration-status")
    if registration_status:
        registration_status.decompose()


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

def fetch_event_cards():

    html = fetch_events_page()
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select('a.events-list__item[href^="/events/"]')

    return [

        parse_event_card(card)

        for card in cards

    ]


def fetch_running_events():
    return [
        event
        for event in fetch_event_cards()
        if is_running_event(event)
        and not is_online_event(event)
    ]


def parse_activities(html):
    soup = BeautifulSoup(html, "html.parser")

    for title in soup.select(".event-details__title"):
        if title.get_text(" ", strip=True) != "Активности":
            continue

        activities_block = title.find_next_sibling(
            "div",
            class_="block-text",
        )

        if activities_block is None:
            return []

        activities = []

        for block in activities_block.select(".event-details-amount"):
            name_element = block.select_one("div")

            if name_element is None:
                continue

            name = name_element.get_text(" ", strip=True)
            distance = parse_distance_from_name(name)

            if distance is None:
                continue

            activities.append({
                "external_id": build_activity_external_id(
                    name,
                    distance,
                ),
                "name": name,
                "distance": distance,
                "discipline_code": "",
                "discipline_name": "",
                "race_datetime": None,
                "hide_race_date": False,
            })

        return activities

    return []



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


def build_activity_external_id(name, distance):
    return f"{name}:{distance}"


def is_online_event(event):
    name = str(event.get("name") or "").lower()

    return (
        "онлайн" in name
        or "online" in name
    )

def is_running_event(event):

    return event["sport"] in RUNNING_SPORTS


def parse_event_page(event_card, html):
    soup = BeautifulSoup(html, "html.parser")

    start_date, end_date = parse_event_date(soup)
    activities = parse_activities(html)

    if start_date is None:
        return None

    if not activities:
        return None

    return {
        "source": "myrace",
        "external_id": event_card["external_id"],
        "name": event_card["name"],
        "city": event_card["city"],
        "date": start_date,
        "activities": activities,
    }


def import_events():
    event_cards = fetch_running_events()
    imported = []

    for event_card in event_cards:
        html = fetch_event_page(event_card["url"])
        clean_event = parse_event_page(event_card, html)

        if clean_event is None:
            continue

        event = save_event(clean_event)
        imported.append(event)

    return imported


def run_import():
    events = import_events()

    print(
        f"MyRace import completed: {len(events)} events"
    )

    return events