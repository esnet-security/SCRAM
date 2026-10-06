"""Define the models used in the route_manager app."""

import datetime
import logging
import re
import uuid as uuid_lib

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse
from netfields import CidrAddressField
from simple_history.models import HistoricalRecords

from typing import Any

logger = logging.getLogger(__name__)

# ASCII-only because channels rejects non-ASCII group names.
word_only = RegexValidator(
    r"^\w+$", "Use only letters, numbers, and underscores.", flags=re.ASCII
)


class Route(models.Model):
    """Define a route as a CIDR route and a UUID."""

    route = CidrAddressField(unique=True)
    uuid = models.UUIDField(db_index=True, default=uuid_lib.uuid4, editable=False)

    def __str__(self):
        """Don't display the UUID, only the route."""
        return str(self.route)

    @staticmethod
    def get_absolute_url():
        """Ensure we use UUID on the API side instead."""
        return reverse("")

class FlowspecRoute(models.Model):
    """Define a flowspec route as a CIDR route and a UUID."""

    source = CidrAddressField(unique=True)
    source_port = models.PositiveIntegerField()
    destination = CidrAddressField(unique=True)
    destination_port = models.PositiveIntegerField()
    protocol = models.PositiveIntegerField() # At what point in the stack should we convert "TCP" to 6, "UDP" to 17, etc.? (Support is in gobgp.py but not in models.py) TODO: make enum
    uuid = models.UUIDField(db_index=True, default=uuid_lib.uuid4, editable=False)

    def __str__(self):
        return f"src {self.source}:{self.source_port} -> dst {self.destination}:{self.destination_port} (proto {self.protocol})"

    @staticmethod
    def get_absolute_url():
        """Ensure we use UUID on the API side instead."""
        return reverse("")


class TranslatorType(models.Model):
    """A type of translator (for example, gobgp). Each translator type has one websocket group."""

    name = models.CharField(
        help_text="One-word name, e.g. gobgp",
        max_length=30,
        unique=True,
        validators=[word_only],
    )
    history = HistoricalRecords()

    def __str__(self) -> str:
        """Only display the name."""
        return self.name

    @property
    def group(self) -> str:
        """The channel layer group that translators of this type listen on."""
        return f"translator_{self.name}"

    @property
    def url(self) -> str:
        """The websocket path translators of this type connect to."""
        return f"/ws/route_manager/{self.group}/"


class ActionType(models.Model):
    """Define a type of action that can be done with a given route. e.g. Block, shunt, redirect, etc."""

    VERBS = ("add", "remove", "check")

    name = models.CharField(
        help_text="One-word description of the action",
        max_length=30,
        unique=True,
        validators=[word_only],
    )
    available = models.BooleanField(
        help_text="Is this a valid choice for new entries?", default=True
    )
    translator_types = models.ManyToManyField(
        TranslatorType,
        blank=True,
        help_text="Which translator types actually perform this action",
    )
    payload = models.JSONField(
        default=dict,
        blank=True,
        help_text='Extra data sent with every message for this action, e.g. {"asn": 65550, "community": 666}',
    )
    history = HistoricalRecords(m2m_fields=[translator_types])

    def __str__(self):
        """Display clearly whether the action is currently available."""
        if not self.available:
            return f"{self.name} (Inactive)"
        return self.name

    def message_type(self, verb) -> str:
        """The message type translators receive, i.e. translator_block_add."""
        return f"translator_{self.name}_{verb}"

    def message(self, verb, route) -> dict[str, Any]:
        """Build the websocket message for a verb and route.

        We also make sure here that the route field is not ever overridden by the payload.
        """

        return {
            "type": self.message_type(verb),
            "message": {**self.payload, "route": str(route)},
        }

    def send_to_translators(self, verb, route, translator_types=None) -> None:
        """Send this action's message to given or all of the translators that it's linked to.

        By default, we just send messages only to the translator types linked to this action, however, we have to be
        able to override this behavior and send to specific translator types instead in the cases of adding/removing
        translator types to the action, so the admin page sends a list of translators to send when that happens.
        """

        # normally we just send to all linked translator_types
        if translator_types is None:
            translator_types = self.translator_types.all()

        groups = [translator_type.group for translator_type in translator_types]
        if not groups:
            logger.warning(
                "Actiontype %s has no translator types, not sending %s for %s",
                self.name,
                verb,
                route,
            )
        message = self.message(verb, route)
        for group in groups:
            async_to_sync(channel_layer.group_send)(group, message)

    def send_active_entries(self, verb, translator_types) -> None:
        """Send every active entry's message for a verb to the given translator types."""
        for entry in self.entry_set.filter(is_active=True).select_related("route"):
            self.send_to_translators(verb, entry.route, translator_types)


class Entry(models.Model):
    """An instance of an action taken on a route."""

    route = models.ForeignKey("Route", on_delete=models.PROTECT, blank=True, null=True)
    flowspec_route = models.ForeignKey("FlowspecRoute", on_delete=models.PROTECT, blank=True, null=True)
    actiontype = models.ForeignKey("ActionType", on_delete=models.PROTECT)
    comment = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    # TODO: fix name if this works
    history = HistoricalRecords()
    when = models.DateTimeField(auto_now_add=True)
    who = models.CharField("Username", default="Unknown", max_length=30)
    originating_scram_instance = models.CharField(
        default="scram_hostname_not_set", max_length=255
    )
    expiration = models.DateTimeField(
        default=datetime.datetime(9999, 12, 31, 0, 0, tzinfo=datetime.UTC)
    )
    expiration_reason = models.CharField(
        help_text="Optional reason for the expiration",
        max_length=200,
        blank=True,
        default="",
    )

    class Meta:
        """Ensure that multiple routes can be added as long as they have different action types."""

        unique_together = ["route", "actiontype"]
        verbose_name_plural = "Entries"

    def __str__(self):
        """Summarize the most important fields to something easily readable."""
        desc = (
            f"{self.route} ({self.actiontype}) from: {self.originating_scram_instance}"
        )
        if not self.is_active:
            desc += " (inactive)"
        return desc

    def delete(self, *args, **kwargs):
        """Set inactive instead of deleting, as we want to ensure a history of entries."""
        if not self.is_active:
            # We've already expired this route, don't send another message
            return
        # We don't actually delete records; we set them to inactive and then tell the translator to remove them
        logger.info("Deactivating %s", self.route)
        self.is_active = False
        self.save()

        self.actiontype.send_to_translators("remove", self.route)

    def get_change_reason(self):
        """Traverse some complex relationships to determine the most recent change reason.

        Returns:
           str: The most recent change reason
        """
        return self.history.order_by("-history_date").first().history_change_reason


class IgnoreEntry(models.Model):
    """Define CIDRs you NEVER want to block (i.e. the "don't shoot yourself in the foot" list)."""

    route = CidrAddressField(unique=True)
    comment = models.CharField(max_length=100)
    history = HistoricalRecords()

    class Meta:
        """Ensure the plural is grammatically correct."""

        verbose_name_plural = "Ignored Entries"

    def __str__(self):
        """Only display the route."""
        return str(self.route)


class Client(models.Model):
    """Any client that would like to hit the API to add entries (e.g. Zeek)."""

    client_name = models.CharField(max_length=50, unique=True)
    uuid = models.UUIDField(default=uuid_lib.uuid4, editable=False, unique=True)
    is_authorized = models.BooleanField(null=True, blank=True, default=False)
    authorized_actiontypes = models.ManyToManyField(ActionType)

    def __str__(self):
        """Only display the client_name."""
        return str(self.client_name)


channel_layer = get_channel_layer()
