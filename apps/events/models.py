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
    begin_datetime = models.DateTimeField(null=True, blank=True, verbose_name="Начало события")
    end_datetime = models.DateTimeField(null=True, blank=True, verbose_name="Окончание события")
    timezone_offset = models.IntegerField(null=True, blank=True, verbose_name="Смещение часового пояса")
    status = models.CharField(choices=STATUS_CHOICES, max_length=200, default='OPEN', verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлен")
    source = models.CharField(max_length=100, blank=True,)
    external_id = models.CharField(max_length=100, blank=True,)
    source_code = models.CharField(max_length=255, blank=True, default='')


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

    def get_activity_dates(self):
        activity_dates = set()

        for activity in self.activities.all():
            if activity.race_datetime is not None:
                activity_dates.add(
                    activity.race_datetime.date()
                )

        return sorted(activity_dates)

    @property
    def is_multiday(self):
        return len(self.get_activity_dates()) > 1



class EventActivity(models.Model):
    event = models.ForeignKey(Event, related_name='activities', on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=False)
    distance = models.DecimalField(max_digits=10, decimal_places=2)
    discipline_code = models.CharField(max_length=100, blank=False, default='')
    discipline_name = models.CharField(max_length=255, blank=False, default='')
    race_datetime = models.DateTimeField(null=True, blank=True)
    hide_race_date = models.BooleanField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    external_id = models.CharField(max_length=100, blank=True,)

    def __str__(self):
        return f'{self.event} — {self.name} ({self.distance} км)'

    class Meta:
        verbose_name = "Активность"
        verbose_name_plural = "Активности"
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

    activity = models.ForeignKey(
        EventActivity,
        related_name='participations',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Активность',
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
        if self.activity:
            if self.activity.event != self.event:
                raise ValidationError(
                    'Выбранная активность не относится к этому ивенту'
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




