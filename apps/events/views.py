from rest_framework.authentication import TokenAuthentication
from rest_framework.generics import ListAPIView, CreateAPIView, DestroyAPIView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.events.models import Event, EventParticipation
from apps.events.serializers import EventSerializer, EventParticipationSerializer
from apps.events.serializers import EventParticipantSerializer



class EventListAPIView(ListAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer



@method_decorator(csrf_exempt, name='dispatch')
class EventParticipationCreateAPIView(CreateAPIView):
    queryset = Event.objects.all()
    serializer_class = EventParticipationSerializer

class EventParticipationDeleteAPIView(DestroyAPIView):
    queryset = EventParticipation.objects.all()
    serializer_class = EventParticipationSerializer


class EventParticipantsApiView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, event_id):

        category = request.query_params.get("category")

        if category not in ("going", "thinking", "company"):

            return Response(

                {

                    "error": (

                        "category must be "

                        "'going', 'thinking' or 'company'"

                    )

                },

                status=status.HTTP_400_BAD_REQUEST,

            )

        event = Event.objects.filter(

            id=event_id

        ).first()

        if not event:

            return Response(

                {"error": "Event not found"},

                status=status.HTTP_404_NOT_FOUND,

            )

        participations = event.participations.select_related(

            "member"

        )

        if category == "going":

            participations = participations.filter(

                status="GOING"

            )

        elif category == "thinking":

            participations = participations.filter(

                status="THINKING"

            )

        elif category == "company":

            participations = participations.filter(

                looking_for_company=True

            )

        members = [

            participation.member

            for participation in participations

        ]

        serializer = EventParticipantSerializer(

            members,

            many=True,

        )

        return Response(

            {

                "event_id": event.id,

                "category": category,

                "count": len(members),

                "participants": serializer.data,

            }

        )


