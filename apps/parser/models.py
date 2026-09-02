from django.db import models

class ParserSource(models.Model):
    name = models.CharField(
        max_length=100,

    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
    )
    base_url = models.URLField(
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return self.name


class ParserRawEvent(models.Model):

    source = models.ForeignKey(
        ParserSource,
        on_delete=models.CASCADE,
        related_name='raw_events',
    )

    external_id = models.CharField(
        max_length=255,
        blank=True,
    )

    source_url = models.URLField(
        blank=True,
    )

    raw_name = models.CharField(
        max_length=255,
        blank=True,
    )

    raw_city = models.CharField(
        max_length=255,
        blank=True,
    )

    raw_date = models.CharField(
        max_length=100,
        blank=True,
    )

    raw_distance = models.JSONField(
        default=list,
        blank=True,
    )

    raw_data = models.JSONField(
        default=dict,
        blank=True,
    )

    parsed_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )


    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['source', 'external_id'],
                name='unique_parser_source_external_id',
            )
        ]


        def __str__(self):
            return (
                f"{self.source}:"
                f"{self.raw_name}"
            )

