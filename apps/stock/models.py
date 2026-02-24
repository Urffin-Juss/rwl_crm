from django.db import models
from django.forms import ValidationError

class Product(models.Model):

    type_choices = [

        ('MEDAL', 'Medal'),
        ('SOCKS', 'Socks'),
        ('ACCESSORY', 'Accessory'),
        ('DRINKWARE', 'Drinkware'),
        ('OTHER', 'Other'),
        ('CLOTHES', 'Clothes'),



    ]


    type = models.CharField(max_length=20, choices=type_choices, verbose_name="Тип товара")
    name = models.CharField(max_length=200, verbose_name="Название")
    variant = models.CharField(max_length=200, null=True, blank=True, verbose_name="Вариант")
    size = models.CharField(max_length=200, null=True, blank=True, verbose_name="Размер")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")


    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

class StockLocation(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название точки")
    location = models.CharField(max_length=200, verbose_name="Локация")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")


    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Точка склада"
        verbose_name_plural = "Точки склада"

class StockItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Товар")
    location = models.ForeignKey(StockLocation, on_delete=models.CASCADE, verbose_name="Точка склада")
    quantity = models.IntegerField(null=True, blank=True, verbose_name="Количество")

    def __str__(self):
        return self.product.name


    class Meta:
        verbose_name = "Остаток"
        verbose_name_plural = "Остатки"
        unique_together = (('product', 'location'),)


    def clean(self):
        if self.quantity < 0:
            raise ValidationError("Количество не может быть отрицательным")
