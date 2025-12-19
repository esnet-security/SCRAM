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
    uuid = serializers.UUIDField()

    class Meta:
        """Maps to the Client model, and specifies the fields exposed by the API."""

        model = Client
        fields = ["client_name", "uuid", "registered_from_ip"]
        read_only_fields = ["registered_from_ip"]


class IsActiveSerializer(serializers.ModelSerializer):
    """Map the serializer to the Entry model."""

    route = serializers.StringRelatedField(source="route.route")

    class Meta:
        """Maps to the Entry model, but limits to the the appropriate fields."""

        model = Entry
        fields = ["is_active", "route"]


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
    originating_scram_instance = serializers.CharField(default="scram_hostname_not_set", read_only=True)
    is_active = serializers.BooleanField(default=True, read_only=True)

    def __init__(self, *args, **kwargs):
        """Make sure we do not allow changing these fields in our put/patch calls."""
        super().__init__(*args, **kwargs)
        if self.instance is not None:
            self.fields["route"].read_only = True
            self.fields["actiontype"].read_only = True
            self.fields["who"].read_only = True

    class Meta:
        """Map to the Entry model, and specify the fields exposed by the API."""

        model = Entry
        fields = [
            "route",
            "actiontype",
            "url",
            "comment",
            "who",
            "expiration",
            "originating_scram_instance",
            "is_active",
        ]

    # This needs to be an instance method since thats expected by DRF
    # ruff: noqa: PLR6301
    def create(self, validated_data):
        """Create or update an Entry, handling duplicates gracefully."""
        route_data = validated_data.pop("route")
        actiontype_name = validated_data.pop("actiontype")
        comment = validated_data.get("comment", "")

        entry, created = Entry.objects.get_or_create(
            route=route_data, actiontype=actiontype_name, defaults=validated_data
        )

        if not created:
            for key, value in validated_data.items():
                setattr(entry, key, value)
            entry.save()
            update_change_reason(entry, comment)

        return entry


class IgnoreEntrySerializer(serializers.ModelSerializer):
    """Map the route to the right field type."""

    route = CustomCidrAddressField()

    class Meta:
        """Maps to the IgnoreEntry model, and specifies the fields exposed by the API."""

        model = IgnoreEntry
        fields = ["route", "comment"]
