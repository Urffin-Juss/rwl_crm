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
    going_count = serializers.SerializerMethodField()
    thinking_count = serializers.SerializerMethodField()
    current_member_status = serializers.SerializerMethodField()




    class Meta:
        model = Event
        fields = (
            'id',
            'name',
            'city',
            'date',
            'status',
            'distances',
            'going_count',
            'thinking_count',
            'current_member_status',
        )




    def get_participants_count(self, obj):
        return obj.participations.count()

    def get_current_member_joined(self, obj):
        request = self.context.get('request')

        if not request:
            return False

        member_id = request.query_params.get('member')

        if not member_id:
            return False

        return obj.participations.filter(
            member_id=member_id
        ).exists()

    def get_going_count(self, obj):
        return obj.participations.filter(
            status='GOING'
        ).count()

    def get_thinking_count(self, obj):
        return obj.participations.filter(
            status='THINKING'
        ).count()

    def get_current_member_status(self, obj):
        request = self.context.get('request')

        if not request:
            return None

        member_id = request.query_params.get('member')

        if not member_id:
            return None

        participation = obj.participations.filter(
            member_id=member_id
        ).first()

        if not participation:
            return None

        return participation.status

class EventParticipationSerializer(serializers.ModelSerializer):

    class Meta:
        model = EventParticipation
        fields = (
            'event',
            'member',
            'distance',
            'status',
            'looking_for_company',
        )

        validators = []

    def validate(self, attrs):
        event = attrs.get('event')
        distance = attrs.get('distance')

        if distance and distance.event != event:
            raise serializers.ValidationError(
                'Выбранная дистанция не относится к этому ивенту'
            )
        return attrs

    def create(self, validated_data):
        member = validated_data.pop('member')
        event = validated_data.pop('event')

        participation, created = EventParticipation.objects.update_or_create(
            member=member,
            event=event,
            defaults=validated_data,
        )

        return participation