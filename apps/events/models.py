from django.db import models
from django.core.exceptions import ValidationError
from django.db import models
from apps.users.models import ClubMember
from django.db.models import Q


class Event(models.Model):

    STATUS_CHOICES = (
    ('OPEN', 'OPEN'),
    ('CLOSED', 'CLOSED'),
    )

    name = models.CharField(max_length=200, verbose_name="Название")
    city = models.CharField(max_length=200, verbose_name="Город")
    date = models.DateField(verbose_name="Дата")
    status = models.CharField(choices=STATUS_CHOICES, max_length=200, default='OPEN', verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлен")
    source = models.CharField(max_length=100, blank=True,)
    external_id = models.CharField(max_length=100, blank=True,)


    def __str__(self):
        return self.name

    class Meta:
        db_table = 'event'
        ordering = ['-date']
        constraints = [
            models.UniqueConstraint(
                fields=['source', 'external_id'],
                condition=~Q(external_id=''),
                name='unique_event_source_external_id',
            )
        ]
        verbose_name = "Ивент"
        verbose_name_plural = "Ивенты"



class EventDistance(models.Model):
    event = models.ForeignKey(Event, related_name='distances', on_delete=models.CASCADE)
    name = models.CharField(max_length=50, blank=False)
    distance = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    external_id = models.CharField(max_length=100, blank=True,)

    def __str__(self):
        return f'{self.event} — {self.name} ({self.distance} км)'

    class Meta:
        verbose_name = "Дистанция"
        verbose_name_plural = "Дистанции"
        constraints = [
            models.UniqueConstraint(
                fields=['event', 'external_id'],
                condition=~Q(external_id=''),
                name='unique_event_event_external_id',
            )
        ]





class EventParticipation(models.Model):
    STATUS_CHOICES = [
        ('GOING', 'Еду'),
        ('THINKING', 'Думаю'),
    ]

    event = models.ForeignKey(
        Event,
        related_name='participations',
        on_delete=models.CASCADE,
        verbose_name='Ивент',
    )

    member = models.ForeignKey(
        ClubMember,
        related_name='participations',
        on_delete=models.CASCADE,
        verbose_name='Участник клуба',
    )

    distance = models.ForeignKey(
        EventDistance,
        related_name='participations',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Дистанция',
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='GOING',
        verbose_name='Статус',
    )

    looking_for_company = models.BooleanField(
        default=False,
        verbose_name='Ищет компанию',
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создано',
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Обновлено',
    )

    def __str__(self):
        return f'{self.member} — {self.event}'

    def clean(self):
        if self.distance:
            if self.distance.event != self.event:
                raise ValidationError(
                    'Выбранная дистанция не относится к этому ивенту'
                )


    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['member', 'event'],
                name='unique_member_event_participation',
            )
        ]

        verbose_name = 'Участие в ивенте'
        verbose_name_plural = 'Участия в ивентах'


