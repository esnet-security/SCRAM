from rest_framework.generics import ListCreateAPIView, RetrieveDestroyAPIView
from rest_framework.permissions import IsAuthenticated

from ..models import Route
from .serializers import RouteSerializer


class RouteView(ListCreateAPIView):
    queryset = Route.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = RouteSerializer
    lookup_field = 'uuid'


class RouteDetailView(RetrieveDestroyAPIView):
    queryset = Route.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = RouteSerializer
    lookup_field = 'route'
