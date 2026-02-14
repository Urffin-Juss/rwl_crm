from django.db import models

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
    variant = models.CharField(max_length=200, null=True)
    size = models.CharField(max_length=200, null=True)
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
    quantity = models.IntegerField()

    def __str__(self):
        return self.product.name


    class Meta:
        unique_together = (('product', 'location'),)
