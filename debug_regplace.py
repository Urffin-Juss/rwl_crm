import os

import django


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()


from apps.parser.services.regplace import import_events


events = import_events()

print()
print("IMPORTED:", len(events))

for event in events:
    print(
        event.id,
        "|",
        event.name,
        "| activities:",
        event.activities.count(),
    )