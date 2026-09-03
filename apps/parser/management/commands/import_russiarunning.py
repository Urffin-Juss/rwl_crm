from django.core.management.base import BaseCommand

from apps.parser.services.russiarunning import run_import


class Command(BaseCommand):
    help = "Импортирует события из RussiaRunning"

    def handle(self, *args, **options):
        run_import()