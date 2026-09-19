from datetime import datetime
from apps.events.models import Event, EventActivity
from typing import Any, Dict





def save_event(clean_event: Dict[str, Any]):

    source = "russiarunning"
    external_id = clean_event.get("external_id")

    event, _ = Event.objects.update_or_create(
        source=source,
        external_id=external_id,
        defaults={
            "name": clean_event.get("name"),
            "city": clean_event.get("city"),
            "source_code": clean_event["source_code"],
            "date": datetime.fromisoformat(clean_event.get("date")).date(),
            "begin_datetime": (datetime.fromisoformat(clean_event["begin_datetime"])
                if clean_event.get("begin_datetime")
                else None),
            "end_datetime": (datetime.fromisoformat(clean_event["end_datetime"])
                if clean_event.get("end_datetime")
                else None),
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