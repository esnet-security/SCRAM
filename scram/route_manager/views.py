from django.shortcuts import render

from .models import Entry


def home_page(request):
    context = {"Entries": Entry.objects.all()}
    return render(request, "route_manager/home.html", context)
