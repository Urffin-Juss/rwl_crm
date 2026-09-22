from datetime import datetime, date
from apps.events.models import Event, EventActivity
from typing import Any, Dict


def normalize_event_date(value):
    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if isinstance(value, str):
        return datetime.fromisoformat(value).date()

    return None


def normalize_event_datetime(value):
    if isinstance(value, datetime):
        return value

    if isinstance(value, date):
        return datetime.combine(
            value,
            datetime.min.time(),
        )

    if isinstance(value, str):
        return datetime.fromisoformat(value)

    return None



def save_event(clean_event: Dict[str, Any]):

    source = clean_event["source"]
    external_id = clean_event.get("external_id")

    event, _ = Event.objects.update_or_create(
        source=source,
        external_id=external_id,
        defaults={
            "name": clean_event.get("name"),
            "city": clean_event.get("city"),
            "source_code": clean_event.get("source_code", ""),
            "date": normalize_event_date(clean_event.get("date")),
            "begin_datetime": normalize_event_datetime(
            clean_event.get("begin_datetime") ),
            "end_datetime": normalize_event_datetime(
                clean_event.get("end_datetime")),
            "timezone_offset": clean_event.get("timezone_offset"),

        }

    )

    save_activities(event, clean_event)
    return event


def save_activities(event, clean_event: Dict[str, Any]) -> None:
    for activity in clean_event.get("activities", []):
        EventActivity.objects.update_or_create(
            event=event,
            external_id=activity.get("external_id"),
            defaults={
                "name": activity.get("name"),
                "distance": activity.get("distance"),
                "discipline_code": activity.get("discipline_code") or "",
                "discipline_name": activity.get("discipline_name") or "",
                "race_datetime": (datetime.fromisoformat(activity["race_datetime"])
                    if activity.get("race_datetime")
                    else None),
                "hide_race_date": activity.get("hide_race_date"),
            },
        )





