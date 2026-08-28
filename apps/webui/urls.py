from django.urls import path

from apps.webui.views import calendar_view


urlpatterns = [
    path('calendar/', calendar_view, name='calendar'),
]