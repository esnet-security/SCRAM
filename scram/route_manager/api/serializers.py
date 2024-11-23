"""Serializers provide mappings between the API and the underlying model."""

import logging

from drf_spectacular.utils import extend_schema_field
from netfields import rest_framework
from rest_framework import serializers
from rest_framework.fields import CurrentUserDefault
from simple_history.utils import update_change_reason

from ..models import ActionType, Client, Entry, IgnoreEntry, Route

logger = logging.getLogger(__name__)


@extend_schema_field(field={"type": "string", "format": "cidr"})
class CustomCidrAddressField(rest_framework.CidrAddressField):
    """Define a wrapper field so swagger can properly handle the inherited field."""



class ActionTypeSerializer(serializers.ModelSerializer):
    """Map the serializer to the model via Meta."""

    class Meta:
        """Maps to the ActionType model, and specifies the fields exposed by the API."""

        model = ActionType
        fields = ["pk", "name", "available"]


class RouteSerializer(serializers.ModelSerializer):
    """Exposes route as a CIDR field."""

    route = CustomCidrAddressField()

    class Meta:
        """Maps to the Route model, and specifies the fields exposed by the API."""

        model = Route
        fields = [
            "route",
        ]


class ClientSerializer(serializers.ModelSerializer):
    """Map the serializer to the model via Meta."""

    class Meta:
        """Maps to the Client model, and specifies the fields exposed by the API."""

        model = Client
        fields = ["hostname", "uuid"]


class EntrySerializer(serializers.HyperlinkedModelSerializer):
    """Due to the use of ForeignKeys, this follows some relationships to make sense via the API."""

    url = serializers.HyperlinkedIdentityField(
        view_name="api:v1:entry-detail",
        lookup_url_kwarg="pk",
        lookup_field="route",
    )
    route = CustomCidrAddressField()
    actiontype = serializers.CharField(default="block")
    if CurrentUserDefault():
        # This is set if we are calling this serializer from WUI
        who = CurrentUserDefault()
    else:
        who = serializers.CharField()
    comment = serializers.CharField()

    class Meta:
        """Maps to the Entry model, and specifies the fields exposed by the API."""

        model = Entry
        fields = ["route", "actiontype", "url", "comment", "who"]

    def get_comment(self, obj):
        """Provide a nicer name for change reason."""
        return obj.get_change_reason()

    def create(self, validated_data):
        """Implement custom logic and validates creating a new route."""
        valid_route = validated_data.pop("route")
        actiontype = validated_data.pop("actiontype")
        comment = validated_data.pop("comment")

        route_instance, created = Route.objects.get_or_create(route=valid_route)
        actiontype_instance = ActionType.objects.get(name=actiontype)
        entry_instance, created = Entry.objects.get_or_create(route=route_instance, actiontype=actiontype_instance)

        logger.debug("Created entry with comment:", comment)
        update_change_reason(entry_instance, comment)

        return entry_instance


class IgnoreEntrySerializer(serializers.ModelSerializer):
    """Map the route to the right field type."""

    route = CustomCidrAddressField()

    class Meta:
        """Maps to the IgnoreEntry model, and specifies the fields exposed by the API."""

        model = IgnoreEntry
        fields = ["route", "comment"]
