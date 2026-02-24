from django.db import models



class Client(models.Model):
    name = models.CharField(max_length=200, verbose_name="ФИО")
    phone = models.CharField(max_length=25, unique=True, db_index=True, verbose_name="Телефон")
    city = models.CharField(max_length=50, null=True, blank=True, verbose_name="Город")
    dob = models.DateField(null=True, blank=True, verbose_name="Дата рождения")
    email = models.EmailField(null=True, blank=True, verbose_name="Email")
    address = models.TextField(null=True, blank=True, verbose_name="Адрес")
    contact = models.TextField(null=True, blank=True, verbose_name="Контакты")
    pets = models.TextField(null=True, blank=True, verbose_name="Питомцы")
    notes = models.TextField(null=True, blank=True, verbose_name="Примечания")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлен")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"



