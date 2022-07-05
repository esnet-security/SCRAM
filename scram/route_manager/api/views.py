import ipaddress
import logging
import netfields

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.db.models import Q
from django.http import Http404
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import ActionType, Entry, History, IgnoreEntry
from .exceptions import IgnoredRoute, PrefixTooLarge
from .serializers import ActionTypeSerializer, EntrySerializer, IgnoreEntrySerializer

channel_layer = get_channel_layer()


class ActionTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ActionType.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = ActionTypeSerializer
    lookup_field = "name"


class IgnoreEntryViewSet(viewsets.ModelViewSet):
    queryset = IgnoreEntry.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = IgnoreEntrySerializer
    lookup_field = "route"


class EntryViewSet(viewsets.ModelViewSet):
    queryset = Entry.objects.filter(is_active=True)
    permission_classes = (IsAuthenticated,)
    serializer_class = EntrySerializer
    lookup_value_regex = ".*"
    http_method_names = ["get", "post", "head", "delete"]

    def perform_create(self, serializer):

        actiontype = serializer.validated_data["actiontype"]
        route = serializer.validated_data["route"]

        min_prefix = getattr(settings, f"V{route.version}_MINPREFIX", 0)
        if route.prefixlen < min_prefix:
            raise PrefixTooLarge()

        # Don't process if we have the entry in the ignorelist
        c = IgnoreEntry.objects.filter(route__net_overlaps=route).count()
        if c >= 1:
            logging.info(f'{route} is in the ignore list, not blocking')
            raise IgnoredRoute
        else:
            # Must match a channel name defined in asgi.py
            async_to_sync(channel_layer.group_send)(
                "xlator_block", {"type": "add_block", "message": {"route": str(route)}}
            )

            serializer.save()

            # create history object with the associated entry including username
            entry = Entry.objects.get(route__route=route, actiontype__name=actiontype)
            history = History(entry=entry, who=self.request.user, why="API perform create")
            history.save()
            entry.is_active = True
            entry.save()

    @staticmethod
    def find_entries(arg, active_filter=None):
        if not arg:
            return Entry.objects.none()

        # Is our argument an integer?
        try:
            pk = int(arg)
            query = Q(pk=pk)
        except ValueError:
            # Maybe a CIDR? We want the ValueError at this point, if not.
            cidr = ipaddress.ip_network(arg, strict=False)

            min_prefix = getattr(settings, f"V{cidr.version}_MINPREFIX", 0)
            if cidr.prefixlen < min_prefix:
                raise PrefixTooLarge()

            query = Q(route__route__net_overlaps=cidr)

        if active_filter is not None:
            query &= Q(is_active=active_filter)

        return Entry.objects.filter(query)

    def retrieve(self, request, pk=None, **kwargs):
        entries = self.find_entries(pk, active_filter=True)
        # TODO: What happens if we get multiple? Is that ok? I think yes, and return them all?
        if entries.count() != 1:
            raise Http404
        serializer = EntrySerializer(entries, many=True, context={"request": request})
        return Response(serializer.data)

    def destroy(self, request, pk=None, *args, **kwargs):
        entries = self.find_entries(pk, active_filter=True)
        # TODO: What happens if we get multiple? Is that ok? I think no, and don't delete them all?
        if entries.count() == 1:
            # create history object with the associated entry including username
            entry = entries[0]
            route = entry.route
            history = History(entry=entry, who=request.user, why="API destroy function")
            history.save()
            entry.is_active = False
            entry.save()

            async_to_sync(channel_layer.group_send)(
                "xlator_block",
                {"type": "remove_block", "message": {"route": str(route)}},
            )

        return Response(status=status.HTTP_204_NO_CONTENT)
