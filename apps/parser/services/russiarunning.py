import requests
from typing import Any, Dict, List


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