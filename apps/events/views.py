from rest_framework.generics import ListAPIView

from apps.events.models import Event
from apps.events.serializers import EventSerializer


class EventListAPIView(ListAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer