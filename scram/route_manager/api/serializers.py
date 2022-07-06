import logging

from netfields import rest_framework
from rest_framework import serializers

from ..models import ActionType, Entry, IgnoreEntry, Route

logger = logging.getLogger(__name__)


class ActionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActionType
        fields = ["pk", "name", "available"]


class RouteSerializer(serializers.ModelSerializer):
    route = rest_framework.CidrAddressField()

    class Meta:
        model = Route
        fields = [
            "route",
        ]


class EntrySerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="api:v1:entry-detail", lookup_url_kwarg="pk", lookup_field="route"
    )
    route = rest_framework.CidrAddressField()
    actiontype = serializers.CharField(default="block")

    class Meta:
        model = Entry
        fields = ["route", "actiontype", "url"]

    def create(self, validated_data):
        valid_route = validated_data.pop("route")
        actiontype = validated_data.pop("actiontype")
        route_instance, created = Route.objects.get_or_create(route=valid_route)
        actiontype_instance = ActionType.objects.get(name=actiontype)
        entry_instance, created = Entry.objects.get_or_create(
            **validated_data, route=route_instance, actiontype=actiontype_instance
        )
        return entry_instance


class IgnoreEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = IgnoreEntry
        fields = ["route", "comment"]
