from django.shortcuts import render
import os
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from apps.users.models import ClubMember
from apps.miniapp.telegram_auth import validate_telegram_init_data
from apps.legal.models import LegalDocument, Consent





def miniapp(request):
    return render(request, 'miniapp/index.html')


class TelegramAuthAPIView(APIView):

    authentication_classes = []
    permission_classes = []


    def post(self, request):

        init_data = request.data.get('init_data')

        if not init_data:
            return Response({'error': 'init_data is required'},
                            status=status.HTTP_400_BAD_REQUEST)

        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')

        if not bot_token:
            return Response(
                {'error': 'TELEGRAM_BOT_TOKEN is not configured'},
                status=status.HTTP_400_BAD_REQUEST)

        telegram_user = validate_telegram_init_data(

            init_data,

            bot_token

        )

        if not telegram_user:
            return Response(
                {"detail": "Invalid telegram data"},
                status=status.HTTP_403_FORBIDDEN
            )

        telegram_id = telegram_user.get("id")

        if not telegram_id:
            return Response(

                {"detail": "Telegram user id is missing"},

                status=status.HTTP_400_BAD_REQUEST

            )

        member, created = ClubMember.objects.get_or_create(

            telegram_id=telegram_id,

            defaults={

                "username": telegram_user.get("username", ""),
                "first_name": telegram_user.get("first_name", ""),
                "last_name": telegram_user.get("last_name", ""),
                "photo_url": telegram_user.get("photo_url", ""),

            }

        )

        required_documents = LegalDocument.objects.filter(
            is_active=True,
            is_required=True,
            requires_acceptance=True
        )

        accepted_document_ids = Consent.objects.filter(
            member=member
        ).values_list(
            "document_id",
            flat=True
        )

        missing_documents = required_documents.exclude(
            id__in=accepted_document_ids
        )

        return Response(

            {

                "member_id": member.id,

                "telegram_id": member.telegram_id,

                "username": member.username,

                "first_name": member.first_name,

                "created": created,

                "required_consents": [

                    {

                        "id": document.id,

                        "title": document.title,

                        "version": document.version,

                        "url": document.external_url,

                    }

                    for document in missing_documents

                ],

            }

        )