import os
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.legal.models import Consent, LegalDocument
from apps.legal.serializers import ConsentCreateSerializer
from apps.miniapp.telegram_auth import validate_telegram_init_data
from apps.users.models import ClubMember
from django.shortcuts import render

def privacy(request):
    return render(request, "legal/privacy.html")


def consent(request):
    return render(request, "legal/consent.html")


def terms(request):
    return render(request, "legal/terms.html")


class ConsentCreateAPIView(APIView):

    authentication_classes = []

    permission_classes = []

    def post(self, request):

        serializer = ConsentCreateSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        document_id = serializer.validated_data["document_id"]

        init_data = serializer.validated_data["init_data"]

        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

        telegram_user = validate_telegram_init_data(

            init_data,

            bot_token

        )

        if not telegram_user:

            return Response(

                {"error": "Invalid Telegram init data"},

                status=status.HTTP_401_UNAUTHORIZED,

            )

        telegram_id = telegram_user.get("id")

        member = ClubMember.objects.filter(

            telegram_id=telegram_id

        ).first()

        if not member:

            return Response(

                {"error": "Club member not found"},

                status=status.HTTP_404_NOT_FOUND,

            )

        document = LegalDocument.objects.get(

            id=document_id

        )

        consent, created = Consent.objects.get_or_create(

            member=member,

            document=document,

        )

        return Response(

            {

                "consent_id": consent.id,

                "document_id": document.id,

                "accepted_at": consent.accepted_at,

                "created": created,

            },

            status=(

                status.HTTP_201_CREATED

                if created

                else status.HTTP_200_OK

            ),

        )