from celery import shared_task
from apps.parser.services.russiarunning import run_import

@shared_task
def import_russiarunning_task():
    run_import()



