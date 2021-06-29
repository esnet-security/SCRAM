from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.shortcuts import render

from ..users.models import User
from .models import ActionType, Entry


def home_page(request):
    context = {"Entries": Entry.objects.all(), "Actiontypes": ActionType.objects.all()}

    if User.objects.count() == 0:
        password = User.objects.make_random_password(
            length=20,
            allowed_chars="abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789!@#$%^&*",
        )
        User.objects.create_superuser("admin", "admin@example.com", password)
        authenticated_admin = authenticate(request, username="admin", password=password)
        login(request, authenticated_admin)
        messages.add_message(
            request,
            messages.SUCCESS,
            f"An admin user was created for you. Please save this password: {password}",
        )
        messages.add_message(
            request,
            messages.INFO,
            "You have been logged in as the admin user",
        )

    return render(request, "route_manager/home.html", context)


def search_entries(request):
    context = {
        "Entries": Entry.objects.filter(route__route=request.POST.get("cidr")),
        "Actiontypes": ActionType.objects.all(),
    }
    return render(request, "route_manager/home.html", context)
