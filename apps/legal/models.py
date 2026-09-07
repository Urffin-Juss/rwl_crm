from django.db import models

from apps.users.models import ClubMember


class LegalDocument(models.Model):

    DOCUMENT_TYPE_CHOICES = [
        ("CONSENT", "Согласие"),
        ("POLICY", "Политика"),
        ("TERMS", "Правила / условия"),
        ("OTHER", "Другой документ"),
    ]

    slug = models.SlugField(
        max_length=100
    )

    title = models.CharField(
        max_length=255
    )

    document_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_TYPE_CHOICES
    )

    version = models.CharField(
        max_length=50
    )

    requires_acceptance = models.BooleanField(
        default=True
    )

    is_required = models.BooleanField(
        default=True
    )

    is_active = models.BooleanField(
        default=True
    )

    file = models.FileField(
        upload_to="legal_documents/",
        blank=True,
        null=True
    )

    external_url = models.URLField(
        blank=True
    )

    published_at = models.DateTimeField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "slug",
                    "version"
                ],
                name="unique_legal_document_version"
            )
        ]

    def __str__(self):
        return f"{self.title} — {self.version}"


class Consent(models.Model):

    member = models.ForeignKey(
        ClubMember,
        on_delete=models.CASCADE,
        related_name="consents"
    )

    document = models.ForeignKey(
        LegalDocument,
        on_delete=models.PROTECT,
        related_name="consents"
    )

    accepted_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "member",
                    "document"
                ],
                name="unique_member_document_consent"
            )
        ]

    def __str__(self):
        return (
            f"{self.member} → "
            f"{self.document}"
        )