from django.urls import path

from apps.events.views import EventListAPIView, EventParticipationCreateAPIView


urlpatterns = [
    path('events/', EventListAPIView.as_view(), name='event-list'),
    path('api/participations/', EventParticipationCreateAPIView.as_view(), name='participation-create'),
]