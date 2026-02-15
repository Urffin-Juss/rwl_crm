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


    type = models.CharField(max_length=20, choices=type_choices)
    name = models.CharField(max_length=200)
    variant = models.CharField(max_length=200, null=True, blank=True)
    size = models.CharField(max_length=200, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.name

class StockLocation(models.Model):
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.name

class StockItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    location = models.ForeignKey(StockLocation, on_delete=models.CASCADE)
    quantity = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.product.name


    class Meta:
        unique_together = (('product', 'location'),)


    def clean(self):
        if self.quantity < 0:
            raise ValidationError("Количество не может быть отрицательным")
