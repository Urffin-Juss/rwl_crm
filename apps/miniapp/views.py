from django.shortcuts import render


def miniapp(request):
    return render(request, 'miniapp/index.html')