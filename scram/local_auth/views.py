from django.shortcuts import render


def login(request):
    return render(request, "account/login.html")


def logout(request):
    return render(request, "account/logout.html")
