import ipaddress
import json

import rest_framework.utils.serializer_helpers
from channels.layers import get_channel_layer
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView

from ..route_manager.api.views import EntryViewSet
from ..users.models import User
from .models import ActionType, Entry

channel_layer = get_channel_layer()


def home_page(request, prefilter=Entry.objects.all()):
    num_entries = settings.RECENT_LIMIT
    if request.user.has_perms(("route_manager.view_entry", "route_manager.add_entry")):
        readwrite = True
    else:
        readwrite = False
    context = {"entries": {}, "readwrite": readwrite}
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
    # Using ipaddress because we needed to turn off strict mode
    # (which netfields uses by default with seemingly no toggle)
    # This caused searches with host bits set to 500 which is bad UX see: 68854ee1ad4789a62863083d521bddbc96ab7025
    addr = ipaddress.ip_network(request.POST.get("cidr"), strict=False)
    # We call home_page because search is just a more specific case of the same view and template to return.
    return home_page(
        request,
        Entry.objects.filter(route__route__net_contained_or_equal=addr),
    )


delete_entry_api = EntryViewSet.as_view({"post": "destroy"})


@require_POST
@permission_required(["route_manager.view_entry", "route_manager.delete_entry"])
def delete_entry(request, pk):
    delete_entry_api(request, pk)
    return redirect("route_manager:home")


class EntryDetailView(PermissionRequiredMixin, DetailView):
    permission_required = ["route_manager.view_entry"]
    model = Entry
    template_name = "route_manager/entry_detail.html"


add_entry_api = EntryViewSet.as_view({"post": "create"})


@permission_required(["route_manager.view_entry", "route_manager.add_entry"])
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
        if isinstance(res.data, rest_framework.utils.serializer_helpers.ReturnDict):
            for k, v in res.data.items():
                for error in v:
                    errors.append(f"'{k}' error: {str(error)}")
        else:
            for k, v in res.data.items():
                errors.append(f"error: {str(v)}")
        messages.add_message(request, messages.ERROR, "<br>".join(errors))
    elif res.status_code == 403:
        messages.add_message(request, messages.ERROR, "Permission Denied")
    else:
        messages.add_message(request, messages.WARNING, f"Something went wrong: {res.status_code}")
    with transaction.atomic():
        home = home_page(request)
    return home


def process_expired(request):
    current_time = timezone.now()
    with transaction.atomic():
        entries_start = Entry.objects.filter(is_active=True).count()
        for obj in Entry.objects.filter(is_active=True, expiration__lt=current_time):
            obj.delete()
        entries_end = Entry.objects.filter(is_active=True).count()

    return HttpResponse(
        json.dumps(
            {
                "entries_deleted": entries_start - entries_end,
                "active_entries": entries_end,
            }
        ),
        content_type="application/json",
    )


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
