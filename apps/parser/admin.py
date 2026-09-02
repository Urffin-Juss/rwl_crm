from django.contrib import admin

from .models import ParserSource, ParserRawEvent


@admin.register(ParserSource)
class ParserSourceAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "is_active",
        "updated_at",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "name",
        "slug",
    )


@admin.register(ParserRawEvent)
class ParserRawEventAdmin(admin.ModelAdmin):
    list_display = (
        "raw_name",
        "source",
        "raw_city",
        "raw_date",
        "parsed_at",
    )

    list_filter = (
        "source",
    )

    search_fields = (
        "raw_name",
        "raw_city",
        "external_id",
        "source_url",
    )

    ordering = (
        "-parsed_at",
    )