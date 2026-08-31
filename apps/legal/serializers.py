from rest_framework import serializers

from apps.legal.models import LegalDocument


class ConsentCreateSerializer(serializers.Serializer):
    document_id = serializers.IntegerField()
    init_data = serializers.CharField()

    def validate_document_id(self, value):
        document = LegalDocument.objects.filter(
            id=value,
            is_active=True,
            requires_acceptance=True,
        ).first()

        if not document:
            raise serializers.ValidationError(
                "Документ не найден или не требует согласия."
            )

        return value