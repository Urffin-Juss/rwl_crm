from django.db import models
from apps.clients.models import Client
from apps.stock.models import Product, StockLocation
from apps.events.models import Event
from django.conf import settings



class Order(models.Model):

    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('confirm', 'Подтвержден'),
        ('processing', 'В обработке'),
        ('completed', 'Завершен'),
        ('cancelled', 'Отменен'),
    ]

    PAYMENT_TYPE_CHOICES = [
        ('cash', 'Наличные'),
        ('card', 'Банковская карта'),
        ('transfer', 'Банковский перевод'),
        ('online', 'Онлайн оплата'),
        ('crypto', 'Криптовалюта'),
    ]


    PAYMENT_STATUS_CHOICES = [
        ('PAID', 'Paid'),
        ('NOT_PAID', 'Not Paid'),
        ('REFUND', 'Refund'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    assigned_packer = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE)
    status = models.CharField(choices=STATUS_CHOICES, default='new', verbose_name='Status')
    payment_status = models.CharField(choices=PAYMENT_STATUS_CHOICES, default='NOT_PAID', verbose_name='Payment Status')
    payment_type = models.CharField(choices=PAYMENT_TYPE_CHOICES, default='cash', verbose_name='Payment Type')
    registration_date = models.DateTimeField(blank=True, null=True)
    distance_text = models.CharField(null=True, blank=True, max_length=250)
    comments = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    stock_location = models.ForeignKey(StockLocation, null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.client)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        """
        MVP-логика:
        - при создании позиции списываем со склада
        - изменение quantity запрещено
        """

        if self.pk:
            old = type(self).objects.only("quantity").get(pk=self.pk)
            if old.quantity != self.quantity:
                raise ValidationError(
                    "Изменение количества запрещено. Удалите позицию и создайте заново."
                )
            return super().save(*args, **kwargs)

        # Создание новой позиции => списание
        if not getattr(self.order, "stock_location", None):
            raise ValidationError("У заказа не выбрана точка склада (stock_location).")

        if self.quantity is None or self.quantity <= 0:
            raise ValidationError("Количество должно быть положительным числом.")

        with transaction.atomic():
            try:
                stock = (
                    StockItem.objects
                    .select_for_update()
                    .get(location=self.order.stock_location, product=self.product)
                )
            except StockItem.DoesNotExist:
                raise ValidationError(
                    f"На точке '{self.order.stock_location}' нет остатков для товара '{self.product}'."
                )

            if stock.quantity < self.quantity:
                raise ValidationError(
                    f"Недостаточно товара '{self.product}'. Доступно: {stock.quantity}, нужно: {self.quantity}."
                )

            stock.quantity -= self.quantity
            stock.save(update_fields=["quantity"])

            return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        При удалении позиции возвращаем товар на склад.
        """
        # Если вдруг у заказа нет stock_location — просто удаляем (не ломаемся)
        if not getattr(self.order, "stock_location", None):
            return super().delete(*args, **kwargs)

        with transaction.atomic():
            try:
                stock = (
                    StockItem.objects
                    .select_for_update()
                    .get(location=self.order.stock_location, product=self.product)
                )
            except StockItem.DoesNotExist:

                return super().delete(*args, **kwargs)

            stock.quantity += self.quantity
            stock.save(update_fields=["quantity"])

            return super().delete(*args, **kwargs)




