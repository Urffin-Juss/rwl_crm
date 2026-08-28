from django.urls import path

from apps.events.views import EventListAPIView


urlpatterns = [
    path('events/', EventListAPIView.as_view(), name='event-list'),
]