"""Define the Views that will handle the HTTP requests."""

import ipaddress
import json
import logging
from datetime import timedelta

import rest_framework.utils.serializer_helpers
from asgiref.sync import async_to_sync
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

from scram.route_manager.models import WebSocketSequenceElement

from ..route_manager.api.views import EntryViewSet
from ..users.models import User
from .models import ActionType, Entry

channel_layer = get_channel_layer()
logger = logging.getLogger(__name__)


def home_page(request, prefilter=None):
    """Return the home page, autocreating a user if none exists."""
    if not prefilter:
        prefilter = Entry.objects.all().select_related("actiontype", "route")
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
    """Wrap the home page with a specified CIDR to restrict Entries to."""
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
    """Wrap delete via the API and redirect to the home page."""
    delete_entry_api(request, pk)
    return redirect("route_manager:home")


class EntryDetailView(PermissionRequiredMixin, DetailView):
    """Define a view for the API to use."""

    permission_required = ["route_manager.view_entry"]
    model = Entry
    template_name = "route_manager/entry_detail.html"


add_entry_api = EntryViewSet.as_view({"post": "create"})


@permission_required(["route_manager.view_entry", "route_manager.add_entry"])
def add_entry(request):
    """Send a WebSocket message when adding a new entry."""
    with transaction.atomic():
        res = add_entry_api(request)

    if res.status_code == 201:  # noqa: PLR2004
        messages.add_message(
            request,
            messages.SUCCESS,
            "Entry successfully added",
        )
    elif res.status_code == 400:  # noqa: PLR2004
        errors = []
        if isinstance(res.data, rest_framework.utils.serializer_helpers.ReturnDict):
            for k, v in res.data.items():
                errors.extend(f"'{k}' error: {error!s}" for error in v)
        else:
            errors.extend(f"error: {v!s}" for v in res.data.values())
        messages.add_message(request, messages.ERROR, "<br>".join(errors))
    elif res.status_code == 403:  # noqa: PLR2004
        messages.add_message(request, messages.ERROR, "Permission Denied")
    else:
        messages.add_message(request, messages.WARNING, f"Something went wrong: {res.status_code}")
    with transaction.atomic():
        home = home_page(request)
    return home  # noqa RET504


def process_updates(request):
    """For entries with an expiration, set them to inactive if expired.

    Grab and announce any new entries added to the shared database by other SCRAM instances.

    Return some simple stats.
    """
    # This operation should be atomic, but we set ATOMIC_REQUESTS=True
    current_time = timezone.now()
    entries_start = Entry.objects.filter(is_active=True).count()

    # More efficient to call objects.filter.delete, but that doesn't call the Entry.delete() method
    for obj in Entry.objects.filter(is_active=True, expiration__lt=current_time):
        obj.delete()
    entries_end = Entry.objects.filter(is_active=True).count()

    # Grab all entries from the last 2 minutes
    cutoff_time = current_time - timedelta(minutes=2)
    new_entries = Entry.objects.filter(when__lt=cutoff_time)

    # Resend new entries that popped up in the database
    # TODO: Find a way to ONLY fire this on the instances that *didn't* create the entry (modify entries model?)
    for entry in new_entries:
        logger.info("$$$$ Found a new fancy entry: %s", entry)
        translator_group = f"translator_{entry.actiontype}"
        elements = list(
            WebSocketSequenceElement.objects.filter(action_type__name=entry.actiontype).order_by("order_num")
        )
        for element in elements:
            msg = element.websocketmessage
            msg.msg_data[msg.msg_data_route_field] = str(entry.route)

            json_to_send = {"type": msg.msg_type, "message": msg.msg_data}
            async_to_sync(channel_layer.group_send)(translator_group, json_to_send)

    return HttpResponse(
        json.dumps(
            {
                "entries_deleted": entries_start - entries_end,
                "active_entries": entries_end,
            },
        ),
        content_type="application/json",
    )


class EntryListView(ListView):
    """Define a view for the API to use."""

    model = Entry
    template_name = "route_manager/entry_list.html"

    @staticmethod
    def get_context_data(**kwargs):
        """Group entries by action type."""
        context = {"entries": {}}
        for at in ActionType.objects.all():
            queryset = Entry.objects.filter(actiontype=at).order_by("-pk")
            context["entries"][at] = {
                "objs": queryset,
                "total": queryset.count(),
            }
        return context
