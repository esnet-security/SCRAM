import ipaddress

import walrus
from django.conf import settings
from django.db.models import Q
from django.http import Http404
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import ActionType, Entry, History
from .exceptions import PrefixTooLarge
from .serializers import ActionTypeSerializer, EntrySerializer


class ActionTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ActionType.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = ActionTypeSerializer
    lookup_field = "name"


class EntryViewSet(viewsets.ModelViewSet):
    queryset = Entry.objects.filter(is_active=True)
    permission_classes = (IsAuthenticated,)
    serializer_class = EntrySerializer
    lookup_value_regex = ".*"
    http_method_names = ["get", "post", "head", "delete"]
    db = walrus.Database(host="redis")

    def perform_create(self, serializer):
        actiontype = serializer.validated_data["actiontype"]
        route = serializer.validated_data["route"]
        self.db.xadd(
            f"{actiontype}_add", {"route": str(route), "actiontype": str(actiontype)}
        )

        serializer.save()

        # Find user somehow?
        # create history object with the associated entry including username

    @staticmethod
    def find_entries(self, arg, active_filter=None):
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
            history = History(entry=entry, who=request.user, why="API destroy function")
            history.save()
            entry.is_active = False
            entry.save()

        return Response(status=status.HTTP_204_NO_CONTENT)
