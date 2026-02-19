from celery import shared_task
from apps.imports.services import ExcelProcessor
from apps.imports.models import ImportBatch

@shared_task
def process_import_batch_task(batch_id):
    """
    Задача для обработки Excel файла в фоне
    """
    try:
        batch = ImportBatch.objects.get(id=batch_id)
        ExcelProcessor.process_batch(batch)
        return f"Batch {batch_id} processed successfully"
    except ImportBatch.DoesNotExist:
        return f"Batch {batch_id} not found"
    except Exception as e:
        return f"Error processing batch {batch_id}: {str(e)}"