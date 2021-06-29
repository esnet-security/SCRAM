from django.contrib import messages
from django.shortcuts import render

from ..users.models import User
from .models import ActionType, Entry


def home_page(request):
    context = {"Entries": Entry.objects.all(), "Actiontypes": ActionType.objects.all()}

    if User.objects.count() == 0:
        password = User.objects.make_random_password()
        User.objects.create_superuser("admin", "admin@example.com", password)
        messages.add_message(
            request,
            messages.SUCCESS,
            f"Admin user created for you.\n Please save this password: {password}",
        )

    return render(request, "route_manager/home.html", context)


def search_entries(request):
    context = {
        "Entries": Entry.objects.filter(route__route=request.POST.get("cidr")),
        "Actiontypes": ActionType.objects.all(),
    }
    return render(request, "route_manager/home.html", context)
