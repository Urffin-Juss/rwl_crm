from django.shortcuts import render


def privacy(request):
    return render(request, "legal/privacy.html")


def consent(request):
    return render(request, "legal/consent.html")


def terms(request):
    return render(request, "legal/terms.html")