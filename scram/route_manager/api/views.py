from rest_framework.generics import (ListCreateAPIView, RetrieveDestroyAPIView)
from rest_framework.permissions import IsAuthenticated

from ..models import Route
from .serializers import IPAddressSerializer


class NetworkView(ListCreateAPIView):
    queryset = Route.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = IPAddressSerializer
    lookup_field = 'uuid'


class NetworkDetailView(RetrieveDestroyAPIView):
    queryset = Route.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = IPAddressSerializer
    lookup_field = 'ip'
