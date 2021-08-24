from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.db import transaction
from django.shortcuts import render
from django.views.generic import ListView

from ..route_manager.api.views import EntryViewSet
from ..users.models import User
from .models import ActionType, Entry


def home_page(request, prefilter=Entry.objects.all()):
    num_entries = settings.RECENT_LIMIT
    context = {"entries": {}}
    for at in ActionType.objects.all():
        queryset = prefilter.filter(actiontype=at).order_by("-pk")
        context["entries"][at] = {
            "objs": queryset[:num_entries],
            "total": queryset.count(),
        }

    if settings.AUTOCREATE_ADMIN:
        if User.objects.count() == 0:
            password = User.objects.make_random_password(
                length=20,
                allowed_chars="abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789!@#$%^&*",
            )
            User.objects.create_superuser("admin", "admin@example.com", password)
            authenticated_admin = authenticate(
                request, username="admin", password=password
            )
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
    # We call home_page because search is just a more specific case of the same view and template to return
    return home_page(
        request,
        Entry.objects.filter(
            route__route__net_contained_or_equal=request.POST.get("cidr")
        ),
    )


add_entry_api = EntryViewSet.as_view({"post": "create"})


def add_entry(request):
    with transaction.atomic():
        res = add_entry_api(request)

    if res.status_code == 201:
        messages.add_message(
            request,
            messages.SUCCESS,
            "Entry successfully added",
        )
    elif res.status_code == 400:
        errors = []
        for k, v in res.data.items():
            for error in v:
                errors.append(f"'{k}' error: {str(error)}")
        messages.add_message(request, messages.ERROR, "<br>".join(errors))
    with transaction.atomic():
        home = home_page(request)
    return home


class EntryListView(ListView):
    model = Entry
    template_name = "route_manager/entry_list.html"

    def get_context_data(self, **kwargs):
        context = {"entries": {}}
        for at in ActionType.objects.all():
            queryset = Entry.objects.filter(actiontype=at).order_by("-pk")
            context["entries"][at] = {
                "objs": queryset,
                "total": queryset.count(),
            }
        return context
