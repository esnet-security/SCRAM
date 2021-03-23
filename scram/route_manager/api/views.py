from rest_framework.generics import (ListCreateAPIView, RetrieveUpdateDestroyAPIView)
from rest_framework.permissions import IsAuthenticated

from ..models import IPAddress
from .serializers import IPAddressSerializer


class IPAddressListCreateAPIView(ListCreateAPIView):
    queryset = IPAddress.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = IPAddressSerializer
    lookup_field = 'uuid'


class IPAddressRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    queryset = IPAddress.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = IPAddressSerializer
    lookup_field = 'ip'
