import ipaddress

import walrus
from django.conf import settings
from django.http import Http404
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import ActionType, Entry
from .exceptions import PrefixTooLarge
from .serializers import ActionTypeSerializer, EntrySerializer


class ActionTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ActionType.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = ActionTypeSerializer
    lookup_field = "name"


class EntryViewSet(viewsets.ModelViewSet):
    queryset = Entry.objects.all()
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

    def retrieve(self, request, pk=None, **kwargs):
        cidr = ipaddress.ip_network(pk, strict=False)
        if cidr.version == 4:
            if cidr.prefixlen < settings.V4_MINPREFIX:
                raise PrefixTooLarge()
        else:
            if cidr.prefixlen < settings.V6_MINPREFIX:
                raise PrefixTooLarge()
        entry = Entry.objects.filter(route__route__net_overlaps=cidr)
        if entry.count() == 0:
            raise Http404
        serializer = EntrySerializer(entry, many=True, context={"request": request})
        return Response(serializer.data)

    def destroy(self, request, pk=None, *args, **kwargs):
        entry = Entry.objects.get(pk=pk)
        actiontype = entry.actiontype.name

        self.db.xadd(
            f"{actiontype}_remove",
            {"route": str(entry.route), "actiontype": actiontype},
        )

        entry.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
