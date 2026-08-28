from rest_framework import serializers
from apps.events.models import EventDistance, Event

class EventDistanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventDistance
        fields = (
            'id',
            'name',
            'distance',
        )


class EventSerializer(serializers.ModelSerializer):

    distances = EventDistanceSerializer(read_only=True, many=True)

    class Meta:
        model = Event
        fields = (
            'id',
            'name',
            'city',
            'date',
            'status',
            'distances',
        )

