from rest_framework import serializers
from apps.events.models import EventDistance, Event, EventParticipation


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
    participants_count = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = (
            'id',
            'name',
            'city',
            'date',
            'status',
            'distances',
            'participants_count'
        )

    def get_participants_count(self, obj):
        return obj.participations.count()

class EventParticipationSerializer(serializers.ModelSerializer):

    class Meta:
        model = EventParticipation
        fields = (
            'event',
            'member',
            'distance',
            'status',
            'looking_company',
        )

    def validate(self, attrs):
        event = attrs.get('event')
        distance = attrs.get('distance')

        if distance and event.distance != event:
            raise serializers.ValidationError(
                'Выбранная дистанция не относится к этому ивенту'
            )
        return attrs