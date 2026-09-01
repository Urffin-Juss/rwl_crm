from rest_framework import serializers
from apps.events.models import EventDistance, Event, EventParticipation
from apps.users.models import ClubMember


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
    current_participation_id = serializers.SerializerMethodField()
    current_member_looking_for_company = serializers.SerializerMethodField()
    looking_for_company_count = serializers.SerializerMethodField()




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
            'looking_for_company_count',
            'current_member_status',
            'current_participation_id',
            'current_member_looking_for_company',
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

    def get_current_participation_id(self, obj):
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

        return participation.id

    def get_current_member_looking_for_company(self, obj):
        request = self.context.get('request')

        if not request:
            return False

        member_id = request.query_params.get('member')

        if not member_id:
            return False

        participation = obj.participations.filter(
            member_id=member_id
        ).first()

        if not participation:
            return False
        return participation.looking_for_company


    def get_looking_for_company_count(self, obj):
        return obj.participations.filter(
            looking_for_company=True
        ).count()






class EventParticipationSerializer(serializers.ModelSerializer):

    class Meta:
        model = EventParticipation
        fields = (
            'id',
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


class EventParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClubMember
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'photo_url',
            'display_name',
        )

    def get_display_name(self, obj):

        full_name = f'{obj.first_name} {obj.last_name}'.strip()

        if full_name:
            return full_name

        if obj.username:
            return f'@{obj.username}'

        return "Участник клуба"