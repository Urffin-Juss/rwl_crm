from rest_framework import serializers
from apps.events.models import EventActivity, Event, EventParticipation
from apps.users.models import ClubMember
from datetime import timedelta, timezone


class EventActivitySerializer(serializers.ModelSerializer):

    race_datetime = serializers.SerializerMethodField()

    def get_race_datetime(self, activity):
        if activity.race_datetime is None:
            return None

        timezone_offset = activity.event.timezone_offset

        if timezone_offset is None:
            timezone_offset = 0

        event_timezone = timezone(

            timedelta(hours=timezone_offset)

        )

        local_datetime = activity.race_datetime.astimezone(

            event_timezone

        )

        return local_datetime.isoformat()


    class Meta:
        model = EventActivity
        fields = (
            'id',
            'name',
            'distance',
            'discipline_code',
            'discipline_name',
            'race_datetime',
            'hide_race_date',
        )


class EventSerializer(serializers.ModelSerializer):

    activities = EventActivitySerializer(read_only=True, many=True)
    going_count = serializers.SerializerMethodField()
    thinking_count = serializers.SerializerMethodField()
    current_member_status = serializers.SerializerMethodField()
    current_participation_id = serializers.SerializerMethodField()
    current_member_looking_for_company = serializers.SerializerMethodField()
    looking_for_company_count = serializers.SerializerMethodField()
    registration_url = serializers.SerializerMethodField()




    class Meta:
        model = Event
        fields = (
            'id',
            'name',
            'city',
            'date',
            'begin_datetime',
            'end_datetime',
            'timezone_offset',
            'status',
            'activities',
            'going_count',
            'thinking_count',
            'looking_for_company_count',
            'current_member_status',
            'current_participation_id',
            'current_member_looking_for_company',
            'registration_url',
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

    def get_registration_url(self, obj):
        if (
                obj.source == "russiarunning"
                and obj.source_code
        ):
            return (
                "https://reg.russiarunning.com/event/"
                f"{obj.source_code}"
            )

        return None





class EventParticipationSerializer(serializers.ModelSerializer):

    class Meta:
        model = EventParticipation
        fields = (
            'id',
            'event',
            'member',
            'activity',
            'status',
            'looking_for_company',
        )

        validators = []

    def validate(self, attrs):
        event = attrs.get('event')
        activity = attrs.get('activity')

        if activity and activity.event != event:
            raise serializers.ValidationError(
                'Выбранная активность не относится к этому ивенту'
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

    display_name = serializers.SerializerMethodField()

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