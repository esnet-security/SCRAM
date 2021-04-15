import logging

from rest_framework import serializers

from ..models import ActionType, Entry, Route

logger = logging.getLogger(__name__)


class ActionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActionType
        fields = ["pk", "name", "available"]


class EntrySerializer(serializers.ModelSerializer):
    route = serializers.IPAddressField()
    actiontype = serializers.CharField(default="block")

    class Meta:
        model = Entry
        fields = "__all__"

    def create(self, validated_data):
        route = validated_data.pop("route")
        actiontype = validated_data.pop("actiontype")
        route_instance, created = Route.objects.get_or_create(route=route)
        actiontype_instance = ActionType.objects.get(name=actiontype)
        entry_instance, created = Entry.objects.get_or_create(
            **validated_data, route=route_instance, actiontype=actiontype_instance
        )
        return entry_instance
