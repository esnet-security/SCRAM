"""Serializers provide mappings between the API and the underlying model."""

import logging

from drf_spectacular.utils import extend_schema_field
from netfields import rest_framework
from rest_framework import serializers
from rest_framework.fields import CurrentUserDefault
from rest_framework.validators import UniqueTogetherValidator
from simple_history.utils import update_change_reason

from ..models import ActionType, Client, Entry, IgnoreEntry, Route, FlowspecRoute, Protocol

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

@extend_schema_field(
    field={
        "oneOf": [
            {"type": "integer", "minimum": 0, "maximum": 255},
            {"type": "string", "enum": [p.name.lower() for p in Protocol]},
        ]
    }
)
class ProtocolField(serializers.Field):
    """Accept an IP protocol as a name (e.g. "tcp") or a number 0-255; always store the number."""

    def to_internal_value(self, value):
        """Normalize a name or number to an int in 0-255."""
        if isinstance(value, bool):
            raise serializers.ValidationError("Invalid protocol")
        if isinstance(value, str) and not value.strip().isdecimal():
            try:
                return Protocol[value.strip().upper()].value
            except KeyError:
                raise serializers.ValidationError(f"Unknown protocol {value!r}; use a name or 0-255") from None
        try:
            number = int(value)
        except (TypeError, ValueError):
            raise serializers.ValidationError("Protocol must be a name or an integer 0-255") from None
        if not 0 <= number <= 255:
            raise serializers.ValidationError("Protocol must be 0-255")
        return number

    def to_representation(self, value):
        """Return the stored number."""
        return value

class FlowspecRouteSerializer(serializers.ModelSerializer):
    """Maps to the FlowspecRoute model."""

    source = CustomCidrAddressField()
    source_port = serializers.IntegerField()
    destination = CustomCidrAddressField()
    destination_port = serializers.IntegerField()
    protocol = ProtocolField()

    class Meta:
        """Maps to the FlowspecRoute model, and specifies the fields exposed by the API."""

        model = FlowspecRoute
        fields = [
            "source",
            "source_port",
            "destination",
            "destination_port",
            "protocol",
        ]
        # we set unique=True on these fields in the model. i was too lazy to create a migration right now
        # thats probably the better fix as this will surely bite us at some point
        extra_kwargs = {
            "source": {"validators": []},
            "destination": {"validators": []}
        }

    # This is very stupid and should not stick around but we cant use the DRF API viewer HTML form otherwise
    # It passes emptry strings for fields without anything listed which breaks errythang
    def get_value(self, dictionary):
        value = super().get_value(dictionary)
        if isinstance(value, dict) and not any(value.values()):
            return serializers.empty
        return value


class ClientSerializer(serializers.ModelSerializer):
    """Map the serializer to the model via Meta."""

    uuid = serializers.UUIDField(required=False)

    class Meta:
        """Maps to the Client model, and specifies the fields exposed by the API."""

        model = Client
        fields = ["client_name", "uuid"]


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
        lookup_field="pk",
    )
    route = CustomCidrAddressField(required=False, allow_null=True)
    flowspec_route = FlowspecRouteSerializer(required=False, allow_null=True)
    actiontype = serializers.CharField(default="block")
    if CurrentUserDefault():
        # This is set if we are calling this serializer from WUI
        who = CurrentUserDefault()
    else:
        who = serializers.CharField()
    comment = serializers.CharField()
    originating_scram_instance = serializers.CharField(
        default="scram_hostname_not_set", read_only=True
    )
    is_active = serializers.BooleanField(default=True, read_only=True)

    def __init__(self, *args, **kwargs):
        """Make sure we do not allow changing these fields in our put/patch calls."""
        super().__init__(*args, **kwargs)
        if self.instance is not None:
            self.fields["route"].read_only = True
            self.fields["flowspec_route"].read_only = True
            self.fields["actiontype"].read_only = True
            self.fields["who"].read_only = True

    class Meta:
        """Map to the Entry model, and specify the fields exposed by the API."""

        model = Entry
        fields = [
            "route",
            "flowspec_route",
            "actiontype",
            "url",
            "comment",
            "who",
            "expiration",
            "originating_scram_instance",
            "is_active",
        ]
        # again, dealing with the unique together in models.py TODO
        validators = []


    # This needs to be an instance method since thats expected by DRF
    # ruff: noqa: PLR6301
    def create(self, validated_data):
        """Create or update an Entry, handling duplicates gracefully."""
        route_data = validated_data.pop("route", None)
        flowspec_data = validated_data.pop("flowspec_route", None)
        actiontype_name = validated_data.pop("actiontype")
        comment = validated_data.get("comment", "")

        if route_data:
            entry, created = Entry.objects.get_or_create(
                route=route_data,
                actiontype=actiontype_name,
                defaults=validated_data,
            )
        else:
            entry, created = Entry.objects.get_or_create(
                flowspec_route=flowspec_data,
                actiontype=actiontype_name,
                defaults=validated_data,
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
