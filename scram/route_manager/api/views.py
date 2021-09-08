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

    def perform_create(self, serializer):
        db = walrus.Database()

        # Add an empty message to create the stream
        actiontype = serializer.validated_data["actiontype"]
        route = serializer.validated_date["route"]
        db.xadd(f"{actiontype}_add", {"route": route, "actiontype": actiontype})

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
        cidr = ipaddress.ip_network(pk, strict=False)
        entry = Entry.objects.filter(route__route__host=cidr)
        entry.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
