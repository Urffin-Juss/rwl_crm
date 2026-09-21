from apps.parser.services.regplace import (
    fetch_running_events,
    fetch_event_page,
    parse_event_page,
)


running_events = fetch_running_events()
parsed_events = []

for event_card in running_events:
    print("Parsing:", event_card["name"])

    html = fetch_event_page(event_card["url"])
    event = parse_event_page(event_card, html)

    parsed_events.append(event)

    print(
        "  date:", event["date"],
        "| activities:", len(event["activities"]),
    )

print()
print("TOTAL:", len(parsed_events))
