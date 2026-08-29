from django.urls import path

from .views import miniapp


urlpatterns = [
    path('', miniapp, name='miniapp'),
]