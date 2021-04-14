from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from ..models import ActionType, Route
from .serializers import ActionTypeSerializer, RouteSerializer


class ActionTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ActionType.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = ActionTypeSerializer
    lookup_field = 'name'


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = RouteSerializer
    lookup_field = 'route'
    lookup_value_regex = '([0-9.]+){3}[0-9]'
    http_method_names = ['get', 'post', 'head', 'delete']
