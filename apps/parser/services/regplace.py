import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs



BASE_URL = "https://reg.place"


def fetch_events_page():

    response = requests.get(

        f"{BASE_URL}/events",

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
        "date_raw": date.get_text(" ", strip=True),
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

    action = card.select_one(".race-card__button")

    distance = None

    for item in card.select(".race-card__meta-item"):

        label = item.select_one(".race-card__meta-label")

        if label and label.get_text(strip=True) == "Дистанция":

            values = list(item.stripped_strings)

            distance = values[-1]

            break

    race_id = None

    if action:

        query = parse_qs(

            urlparse(action.get("href")).query

        )

        race_id = query.get("race_id", [None])[0]

    return {
        "external_id": race_id,
        "name": title.get_text(" ", strip=True),
        "distance": parse_distance(distance),
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