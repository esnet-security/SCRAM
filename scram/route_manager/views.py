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
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
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
        queryset_active = prefilter.filter(actiontype=at, is_active=True).order_by("-pk")
        context["entries"][at] = {
            "objs": queryset_active[:num_entries],
            "active": queryset_active.count(),
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
    try:
        addr = ipaddress.ip_network(request.POST.get("cidr"), strict=False)
    except ValueError:
        try:
            # leading space was breaking ipaddress module
            str_addr = str(request.POST.get("cidr")).strip()
            addr = ipaddress.ip_network(str_addr, strict=False)
        except ValueError:
            messages.add_message(request, messages.ERROR, "Search query was blank")
            return redirect("route_manager:home")

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
        home_page(request)
    return redirect("route_manager:home")


def process_updates(request):
    """For entries with an expiration, set them to inactive if expired.

    Grab and announce any new entries added to the shared database by other SCRAM instances.

    Return some simple stats.
    """
    logger.debug("Executing process_updates")
    # This operation should be atomic, but we set ATOMIC_REQUESTS=True
    current_time = timezone.now()
    entries_start = Entry.objects.filter(is_active=True).count()

    logger.debug("Looking for expired entries")
    # More efficient to call objects.filter.delete, but that doesn't call the Entry.delete() method
    for obj in Entry.objects.filter(is_active=True, expiration__lt=current_time):
        logger.info("Found expired entry: %s. Deleting now", obj)
        obj.delete()
    entries_end = Entry.objects.filter(is_active=True).count()

    logger.debug("Looking for new entries from other SCRAM instances")
    # Grab all entries from the last 2 minutes that originated from a different SCRAM instance.
    cutoff_time = current_time - timedelta(minutes=2)
    new_entries = Entry.objects.filter(when__gt=cutoff_time).exclude(
        originating_scram_instance=settings.SCRAM_HOSTNAME
    )

    # Resend new entries that popped up in the database
    for entry in new_entries:
        logger.info("Processing new entry: %s", entry)
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
                "remote_entries_added": new_entries.count(),
            },
        ),
        content_type="application/json",
    )


class EntryListView(ListView):
    """Define a view for the API to use."""

    model = Entry
    template_name = "route_manager/entry_list.html"
    context_object_name = "object_list"
    paginate_by = settings.PAGINATION_SIZE

    def get_context_data(self, **kwargs):
        """Add action type grouping to context with separate paginators."""
        context = super().get_context_data(**kwargs)

        current_page_params = {}
        for key, value in self.request.GET.items():
            if key.startswith("page_"):
                current_page_params[key] = value

        entries_by_type = {}

        # Get all available action types
        for at in ActionType.objects.filter(available=True):
            queryset = Entry.objects.filter(actiontype=at, is_active=True).order_by("-pk")

            # Create a paginator for this action type
            paginator = Paginator(queryset, settings.PAGINATION_SIZE)

            # Get page number from request with a unique parameter name per type
            page_param = f"page_{at.name.lower()}"
            page_number = self.request.GET.get(page_param, 1)

            try:
                page_obj = paginator.page(page_number)
            except (PageNotAnInteger, EmptyPage):
                page_obj = paginator.page(1)

            entries_by_type[at] = {
                "total": queryset.count(),
                "objs": page_obj,
                "page_param": page_param,
                "page_number": page_number,
                "current_page_params": current_page_params.copy(),
            }

        context["entries"] = entries_by_type
        return context
