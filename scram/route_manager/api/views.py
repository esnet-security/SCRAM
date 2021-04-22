from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from ..models import ActionType, Entry
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
    lookup_field = "route__route"
    lookup_value_regex = ".*"
    http_method_names = ["get", "post", "head", "delete"]
