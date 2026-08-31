from django.urls import path

from .views import miniapp, TelegramAuthAPIView


urlpatterns = [
    path('', miniapp, name='miniapp'),
    path('auth', TelegramAuthAPIView.as_view(), name='telegram_auth'),

]