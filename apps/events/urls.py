from django.urls import path

from apps.events.views import EventListAPIView, EventParticipationCreateAPIView, EventParticipationDeleteAPIView

urlpatterns = [
    path('events/', EventListAPIView.as_view(), name='event-list'),
    path('participations/', EventParticipationCreateAPIView.as_view(), name='participation-create'),
    path(
        'participations/<int:pk>/',
        EventParticipationDeleteAPIView.as_view(),
        name='participation-delete',
    ),
]