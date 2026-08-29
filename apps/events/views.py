from rest_framework.generics import ListAPIView, CreateAPIView

from apps.events.models import Event
from apps.events.serializers import EventSerializer, EventParticipationSerializer


class EventListAPIView(ListAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer


class EventParticipationCreateAPIView(CreateAPIView):
    queryset = Event.objects.all()
    serializer_class = EventParticipationSerializer