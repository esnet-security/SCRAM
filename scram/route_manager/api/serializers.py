from rest_framework import serializers

from ..models import ActionType, Route


class ActionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActionType
        fields = ['name', 'available']


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ['route', 'uuid']
