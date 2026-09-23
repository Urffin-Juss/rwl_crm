from celery import shared_task
from apps.parser.services.russiarunning import (
    run_import as run_russiarunning_import,
)

from apps.parser.services.regplace import (
    run_import as run_regplace_import,
)

from apps.parser.services.myrace import (
    run_import as run_myrace_import,
)

@shared_task
def import_russiarunning_task():
    run_russiarunning_import()


@shared_task
def import_regplace_task():
    run_regplace_import()

@shared_task
def import_myrace_task():
    run_myrace_import()





