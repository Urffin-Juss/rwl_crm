from django.contrib.auth.decorators import login_required
from django.shortcuts import render

def landing(request):
    return render(request, "webui/landing.html")

@login_required
def workspace(request):
    return render(request, "webui/workspace.html")