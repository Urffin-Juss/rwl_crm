import requests
from typing import Any, Dict, List
from apps.parser.services.event_writer import save_event



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


RUNNING_DISCIPLINE_CODES = {
    "run",
    "trail",
    "run-relay",
}


def cleanup_activities(
    race_items: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Очищает список дистанций RussiaRunning
    и оставляет только нужные нам поля.
    """

    clean_data = []

    for race_item in race_items:
        if race_item.get("disciplineCode") not in RUNNING_DISCIPLINE_CODES:
            continue

        code = race_item.get("code", "")
        name = str(race_item.get("name") or "").strip().lower()

        if code == "online" or code.startswith("online_") or name == "online":
            continue

        clean_item = {
            "external_id": race_item.get("id"),
            "name": race_item.get("name"),
            "distance": race_item.get("distance"),
            "discipline_code": race_item.get("disciplineCode"),
            "discipline_name": race_item.get("disciplineName"),
            "race_datetime": race_item.get("raceDate"),
            "hide_race_date": race_item.get("hideRaceDate"),
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
        "source": 'russiarunning',
        "external_id": event.get("id"),
        "name": event.get("title"),
        "city": event.get("cityName") or event.get("place") or "",
        "date": event.get("beginDate"),
        "begin_datetime": event.get("beginDate"),
        "end_datetime": event.get("endDate"),
        "timezone_offset": event.get("timeZoneOffset"),
        "source_code": event.get("code", ""),
        "activities": cleanup_activities(
            event.get("raceItems", [])
        ),
    }

    return clean_event






def import_events(events: List[Dict[str, Any]]) -> None:
    for raw_event in events:
        clean_event = parse_event(raw_event)
        save_event(clean_event)




def fetch_all_events(
    take: int = 12,
    skip: int = 0,
) -> List[Dict[str, Any]]:

    all_events = []

    while True:
        page = fetch_events(
            take=take,
            skip=skip,
        )

        if not page:
            break

        all_events.extend(page)

        skip += take

    return all_events


def run_import() -> None:
    all_events = fetch_all_events()
    import_events(all_events)
