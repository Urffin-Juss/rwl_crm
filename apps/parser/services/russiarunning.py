import requests
from typing import Any, Dict, List

from django.db.models import JSONField


def fetch_events(
    take: int = 12,
    skip: int = 0,
) -> List[Dict[str, Any]]:
    """
    Получает список событий из API RussiaRunning.

    Args:
        take: Количество событий для загрузки.
        skip: Количество событий, которые нужно пропустить.

    Returns:
        Список событий RussiaRunning.

    Raises:
        RuntimeError: Если запрос к API завершился ошибкой.
        ValueError: Если API вернул ответ неожиданного формата.
    """

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


def parse_event(event: Dict[str, Any]) -> Dict[str, Any]:

    if not isinstance(event, dict):

        raise ValueError("Событие должно быть словарём")

    return {

        "external_id": event.get("id"),

        "name": event.get("title"),

        "city": event.get("cityName") or event.get("place") or "",

        "date": event.get("beginDate"),

        "distances": event.get("raceItems", []),

    }

from typing import Any, Dict, List


def cleanup_distances(
    race_items: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Очищает список дистанций RussiaRunning
    и оставляет только нужные нам поля.
    """

    clean_data = []

    for race_item in race_items:
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


