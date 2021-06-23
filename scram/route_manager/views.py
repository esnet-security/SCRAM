from django.shortcuts import render

from .models import ActionType, Entry


def home_page(request):
    context = {"Entries": Entry.objects.all(), "Actiontypes": ActionType.objects.all()}
    return render(request, "route_manager/home.html", context)


def search_entries(request):
    context = {
        "Entries": Entry.objects.filter(route__route=request.POST.get("cidr")),
        "Actiontypes": ActionType.objects.all(),
    }
    return render(request, "route_manager/home.html", context)
