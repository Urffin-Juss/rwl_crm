from django.db import models
from config import settings
from django.utils import timezone


class ImportBatch(models.Model):
    STATUS_NEW = "NEW"
    STATUS_PROCESSING = "PROCESSING"
    STATUS_DONE = "DONE"
    STATUS_FAILED = "FAILED"


    STATUS_CHOICES = [
        ('NEW', 'New'),
        ('PROCESSING', 'Processing'),
        ('DONE', 'Done'),
        ('FAILED', 'Failed'),
    ]


    event = models.ForeignKey('events.Event', on_delete=models.CASCADE, verbose_name="Ивент")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Кто загрузил")
    file_name = models.CharField(max_length=255, verbose_name="Имя файла")
    file_hash = models.CharField(max_length=255, verbose_name="Хеш файла")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW, verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлен")
    file = models.FileField(upload_to='imports/', verbose_name="Файл")
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name="Обработан")
    result = models.JSONField(null=True, blank=True, default=dict, verbose_name="Результат")
    error = models.TextField(blank=True, default="", verbose_name="Ошибка")


    def __str__(self):
        return str(self.event)

    class Meta:
        verbose_name = "Пакет импорта"
        verbose_name_plural = "Пакеты импорта"
        constraints = [
            models.UniqueConstraint(
                fields=['event', 'file_hash'],
                name='unique_event_file_hash'
            )
        ]

    def process(self):
        from apps.imports.services import ExcelProcessor
        return ExcelProcessor.process_batch(self)

    def process_batch(self) -> dict:
        from apps.imports.services import ExcelProcessor

        self.status = self.STATUS_PROCESSING
        self.error = ""
        self.result = {}
        self.save(update_fields=["status", "error", "result"])

        try:
            result = ExcelProcessor.process_batch(self)  # возвращает dict
        except Exception as e:
            self.status = self.STATUS_FAILED
            self.processed_at = timezone.now()
            self.error = str(e)
            self.save(update_fields=["status", "processed_at", "error"])
            raise  # чтобы админка показала сообщение об ошибке

        self.status = self.STATUS_DONE
        self.processed_at = timezone.now()
        self.result = result or {}
        self.save(update_fields=["status", "processed_at", "result"])
        return self.result


class RawExcelRow(models.Model):
    batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE, verbose_name="Пакет импорта")
    row_number = models.IntegerField(verbose_name="Номер строки")
    raw_data = models.JSONField(verbose_name="Сырые данные")
    linked_client = models.ForeignKey('clients.Client', on_delete=models.SET_NULL, null=True, verbose_name="Связанный клиент")
    linked_order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, verbose_name="Связанный заказ")
    error_message = models.TextField(null=True, blank=True, verbose_name="Текст ошибки")

    def __str__(self):
        return str(self.batch)

    class Meta:
        verbose_name = "Строка Excel (raw)"
        verbose_name_plural = "Строки Excel (raw)"
        constraints = [
            models.UniqueConstraint(
                fields=['batch', 'row_number'],
                name='unique_row_per_import'
            )
        ]
