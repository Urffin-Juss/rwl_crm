from django.urls import path

from . import views


urlpatterns = [
    path("privacy/", views.privacy, name="privacy"),
    path("consent/", views.consent, name="consent"),
    path("terms/", views.terms, name="terms"),
]