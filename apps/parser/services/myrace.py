import requests
from bs4 import BeautifulSoup
import re

BASE_URL = "https://myrace.info"


RUNNING_SPORTS = {
    "Бег",
    "Трейл",
    "Скайраннинг",
}







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