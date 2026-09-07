from django.contrib import admin

from .models import LegalDocument, Consent


@admin.register(LegalDocument)
class LegalDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "slug",
        "version",
        "document_type",
        "requires_acceptance",
        "is_required",
        "is_active",
        "published_at",
    )

    list_filter = (
        "document_type",
        "requires_acceptance",
        "is_required",
        "is_active",
    )

    search_fields = (
        "title",
        "slug",
        "version",
    )

    ordering = (
        "slug",
        "-created_at",
    )


@admin.register(Consent)
class ConsentAdmin(admin.ModelAdmin):
    list_display = (
        "member",
        "document",
        "accepted_at",
    )

    list_filter = (
        "document",
        "accepted_at",
    )

    search_fields = (
        "member__username",
        "member__first_name",
        "member__last_name",
        "document__title",
        "document__slug",
    )

    readonly_fields = (
        "accepted_at",
    )

    ordering = (
        "-accepted_at",
    )