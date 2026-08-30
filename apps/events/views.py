from rest_framework.generics import ListAPIView, CreateAPIView, DestroyAPIView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from apps.events.models import Event, EventParticipation
from apps.events.serializers import EventSerializer, EventParticipationSerializer


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