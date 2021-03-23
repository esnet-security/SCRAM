from rest_framework.generics import (ListCreateAPIView, RetrieveDestroyAPIView)
from rest_framework.permissions import IsAuthenticated

from ..models import IPAddress
from .serializers import IPAddressSerializer


class NetworkView(ListCreateAPIView):
    queryset = IPAddress.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = IPAddressSerializer
    lookup_field = 'uuid'


class NetworkDetailView(RetrieveDestroyAPIView):
    queryset = IPAddress.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = IPAddressSerializer
    lookup_field = 'ip'
