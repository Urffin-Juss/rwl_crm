import requests
from typing import Any, Dict, List
from datetime import datetime
from apps.events.models import Event, EventDistance


def fetch_events(
    take: int = 12,
    skip: int = 0,
) -> List[Dict[str, Any]]:


    api_url = "https://reg.russiarunning.com/api/events/list"

    payload = {
        "page": {
            "take": take,
            "skip": skip,
        },
        "language": "ru",
        "filter": {
            "eventsLoaderType": 0,
            "search": "",
            "championshipIds": [],
        },
    }

    try:
        response = requests.post(
            api_url,
            json=payload,
            timeout=10,
        )
        response.raise_for_status()

    except requests.RequestException as exc:
        raise RuntimeError(
            f"Ошибка запроса к RussiaRunning: {exc}"
        ) from exc

    try:
        data = response.json()
    except requests.JSONDecodeError as exc:
        raise ValueError(
            "RussiaRunning вернул некорректный JSON"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(
            "RussiaRunning вернул ответ неожиданного формата"
        )

    events = data.get("list")

    if not isinstance(events, list):
        raise ValueError(
            "В ответе RussiaRunning отсутствует список событий"
        )

    return events





def cleanup_distances(
    race_items: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Очищает список дистанций RussiaRunning
    и оставляет только нужные нам поля.
    """

    clean_data = []

    for race_item in race_items:
        if race_item.get("disciplineCode") != "run":
            continue

        code = race_item.get("code", "")

        if str(code).startswith("online_"):
            continue

        clean_item = {
            "external_id": race_item.get("id"),
            "name": race_item.get("name"),
            "distance": race_item.get("distance"),
        }

        clean_data.append(clean_item)

    return clean_data


def parse_event(
    event: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Преобразует событие RussiaRunning
    в формат, который нужен нашему приложению.
    """

    clean_event = {
        "external_id": event.get("id"),
        "name": event.get("title"),
        "city": event.get("cityName") or event.get("place") or "",
        "date": event.get("beginDate"),
        "distances": cleanup_distances(
            event.get("raceItems", [])
        ),
    }

    return clean_event


def save_event(clean_event: Dict[str, Any]):

    source = "russiarunning"
    external_id = clean_event.get("external_id")

    event, _ = Event.objects.update_or_create(
        source=source,
        external_id=external_id,
        defaults={
            "name": clean_event.get("name"),
            "city": clean_event.get("city"),
            "date": datetime.fromisoformat(clean_event.get("date")).date(),
        }

    )

    save_distances(event, clean_event)
    return event


def save_distances(event, clean_event: Dict[str, Any]) -> None:
    for distance in clean_event.get("distances", []):
        EventDistance.objects.update_or_create(
            event=event,
            external_id=distance.get("external_id"),
            defaults={
                "name": distance.get("name"),
                "distance": distance.get("distance"),
            },
        )



def import_events(events: List[Dict[str, Any]]) -> None:
    for raw_event in events:
        clean_event = parse_event(raw_event)
        save_event(clean_event)


