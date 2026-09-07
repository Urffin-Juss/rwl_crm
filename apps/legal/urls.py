from django.urls import path
from .views import ConsentCreateAPIView
from . import views


urlpatterns = [
    path("privacy/", views.privacy, name="privacy"),
    path("consent/", views.consent, name="consent"),
    path("terms/", views.terms, name="terms"),
    path("consents/", ConsentCreateAPIView.as_view(), name="consent_create",),


]