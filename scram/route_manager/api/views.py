"""Views provide mappings between the underlying model and how they're listed in the API."""

import ipaddress
import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import Http404
from django.utils.dateparse import parse_datetime
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from ..models import ActionType, Client, Entry, IgnoreEntry, WebSocketSequenceElement
from .exceptions import ActiontypeNotAllowed, IgnoredRoute, PrefixTooLarge
from .serializers import ActionTypeSerializer, ClientSerializer, EntrySerializer, IgnoreEntrySerializer

channel_layer = get_channel_layer()


@extend_schema(
    description="API endpoint for actiontypes",
    responses={200: ActionTypeSerializer},
)
class ActionTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """Lookup ActionTypes by name when authenticated, and bind to the serializer."""

    queryset = ActionType.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = ActionTypeSerializer
    lookup_field = "name"


@extend_schema(
    description="API endpoint for ignore entries",
    responses={200: IgnoreEntrySerializer},
)
class IgnoreEntryViewSet(viewsets.ModelViewSet):
    """Lookup IgnoreEntries by route when authenticated, and bind to the serializer."""

    queryset = IgnoreEntry.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = IgnoreEntrySerializer
    lookup_field = "route"


@extend_schema(
    description="API endpoint for clients",
    responses={200: ClientSerializer},
)
class ClientViewSet(viewsets.ModelViewSet):
    """Lookup Client by hostname on POSTs regardless of authentication, and bind to the serializer."""

    queryset = Client.objects.all()
    # We want to allow a client to be registered from anywhere
    permission_classes = (AllowAny,)
    serializer_class = ClientSerializer
    lookup_field = "hostname"
    http_method_names = ["post"]


@extend_schema(
    description="API endpoint for entries",
    responses={200: EntrySerializer},
)
class EntryViewSet(viewsets.ModelViewSet):
    """Lookup Entry when authenticated, and bind to the serializer."""

    queryset = Entry.objects.filter(is_active=True)
    permission_classes = (IsAuthenticated,)
    serializer_class = EntrySerializer
    lookup_value_regex = ".*"
    http_method_names = ["get", "post", "head", "delete"]

    def get_permissions(self):
        """Override the permissions classes for POST method since we want to accept Entry creates from any client.

        Note: We make authorization decisions on whether to actually create the object in the perform_create method
        later.
        """
        if self.request.method == "POST":
            return [AllowAny()]
        return super().get_permissions()

    def perform_create(self, serializer):
        """Create a new Entry, causing that route to receive the actiontype (i.e. block)."""
        actiontype = serializer.validated_data["actiontype"]
        route = serializer.validated_data["route"]
        if self.request.user.username:
            # This is set if our request comes through the WUI path
            who = self.request.user.username
        else:
            # This is set if we pass the "who" through the json data in an API call (like from Zeek)
            who = serializer.validated_data["who"]
        comment = serializer.validated_data["comment"]
        tmp_exp = self.request.data.get("expiration", "")

        try:
            expiration = parse_datetime(tmp_exp)  # noqa: F841
        except ValueError:
            logging.warning("Could not parse expiration DateTime string:", tmp_exp)

        # Make sure we put in an acceptable sized prefix
        min_prefix = getattr(settings, f"V{route.version}_MINPREFIX", 0)
        if route.prefixlen < min_prefix:
            raise PrefixTooLarge()

        # Make sure this client is authorized to add this entry with this actiontype
        if self.request.data.get("uuid"):
            client_uuid = self.request.data["uuid"]
            authorized_actiontypes = Client.objects.filter(uuid=client_uuid).values_list(
                "authorized_actiontypes__name",
                flat=True,
            )
            authorized_client = Client.objects.filter(uuid=client_uuid).values("is_authorized")
            if not authorized_client or actiontype not in authorized_actiontypes:
                logging.debug("Client", client_uuid, "actiontypes:", authorized_actiontypes)
                logging.info(client_uuid, "is not allowed to add an entry to the", actiontype, "list")
                raise ActiontypeNotAllowed()
        elif not self.request.user.has_perm("route_manager.can_add_entry"):
            raise PermissionDenied()

        # Don't process if we have the entry in the ignorelist
        overlapping_ignore = IgnoreEntry.objects.filter(route__net_overlaps=route)
        if overlapping_ignore.count():
            ignore_entries = []
            for ignore_entry in overlapping_ignore.values():
                ignore_entries.append(str(ignore_entry["route"]))
            logging.info("Cannot proceed adding", route, " The ignore list contains", ignore_entries)
            raise IgnoredRoute
        else:
            elements = WebSocketSequenceElement.objects.filter(action_type__name=actiontype).order_by("order_num")
            if not elements:
                logging.warning("No elements found for actiontype:", actiontype)

            for element in elements:
                msg = element.websocketmessage
                msg.msg_data[msg.msg_data_route_field] = str(route)
                # Must match a channel name defined in asgi.py
                async_to_sync(channel_layer.group_send)(
                    f"translator_{actiontype}",
                    {"type": msg.msg_type, "message": msg.msg_data},
                )

            serializer.save()

            entry = Entry.objects.get(route__route=route, actiontype__name=actiontype)
            if expiration:
                entry.expiration = expiration
            entry.who = who
            entry.is_active = True
            entry.comment = comment
            logging.info("Created entry:", entry)
            entry.save()

    @staticmethod
    def find_entries(arg, active_filter=None):
        """Query entries either by pk or overlapping route."""
        if not arg:
            return Entry.objects.none()

        # Is our argument an integer?
        try:
            pk = int(arg)
            query = Q(pk=pk)
        except ValueError as exc:
            # Maybe a CIDR? We want the ValueError at this point, if not.
            cidr = ipaddress.ip_network(arg, strict=False)

            min_prefix = getattr(settings, f"V{cidr.version}_MINPREFIX", 0)
            if cidr.prefixlen < min_prefix:
                raise PrefixTooLarge() from exc

            query = Q(route__route__net_overlaps=cidr)

        if active_filter is not None:
            query &= Q(is_active=active_filter)

        return Entry.objects.filter(query)

    def retrieve(self, request, pk=None, **kwargs):
        """Retrieve a single route."""
        entries = self.find_entries(pk, active_filter=True)
        # TODO: What happens if we get multiple? Is that ok? I think yes, and return them all?
        if entries.count() != 1:
            raise Http404
        serializer = EntrySerializer(entries, many=True, context={"request": request})
        return Response(serializer.data)

    def destroy(self, request, pk=None, *args, **kwargs):
        """Only delete active (e.g. announced) entries."""
        for entry in self.find_entries(pk, active_filter=True):
            entry.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
