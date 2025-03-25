"""Define the models used in the route_manager app."""

import datetime
import logging
import uuid as uuid_lib

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import models
from django.urls import reverse
from netfields import CidrAddressField
from simple_history.models import HistoricalRecords

logger = logging.getLogger(__name__)


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


class ActionType(models.Model):
    """Define a type of action that can be done with a given route. e.g. Block, shunt, redirect, etc."""

    name = models.CharField(help_text="One-word description of the action", max_length=30)
    available = models.BooleanField(help_text="Is this a valid choice for new entries?", default=True)
    history = HistoricalRecords()

    def __str__(self):
        """Display clearly whether the action is currently available."""
        if not self.available:
            return f"{self.name} (Inactive)"
        return self.name


class WebSocketMessage(models.Model):
    """Define a single message sent to downstream translators via WebSocket."""

    msg_type = models.CharField("The type of the message", max_length=50)
    msg_data = models.JSONField("The JSON payload. See also msg_data_route_field.", default=dict)
    msg_data_route_field = models.CharField(
        "The key in the JSON payload whose value will contain the route being acted on.",
        default="route",
        max_length=25,
    )

    def __str__(self):
        """Display clearly what the fields are used for."""
        return f"{self.msg_type}: {self.msg_data} with the route in key {self.msg_data_route_field}"


class WebSocketSequenceElement(models.Model):
    """In a sequence of messages, define a single element."""

    websocketmessage = models.ForeignKey("WebSocketMessage", on_delete=models.CASCADE)
    order_num = models.SmallIntegerField(
        "Sequences are sent from the smallest order_num to the highest. "
        "Messages with the same order_num could be sent in any order",
        default=0,
    )

    VERB_CHOICES = [
        ("A", "Add"),
        ("C", "Check"),
        ("R", "Remove"),
    ]
    verb = models.CharField(max_length=1, choices=VERB_CHOICES)

    action_type = models.ForeignKey("ActionType", on_delete=models.CASCADE)

    def __str__(self):
        """Summarize the fields into something short and readable."""
        return (
            f"{self.websocketmessage} as order={self.order_num} for "
            f"{self.verb} actions on actiontype={self.action_type}"
        )


class Entry(models.Model):
    """An instance of an action taken on a route."""

    route = models.ForeignKey("Route", on_delete=models.PROTECT)
    actiontype = models.ForeignKey("ActionType", on_delete=models.PROTECT)
    comment = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    # TODO: fix name if this works
    history = HistoricalRecords(related_name="entry_history")
    when = models.DateTimeField(auto_now_add=True)
    who = models.CharField("Username", default="Unknown", max_length=30)
    originating_scram_instance = models.CharField(default="scram_hostname_not_set", max_length=255)
    expiration = models.DateTimeField(default=datetime.datetime(9999, 12, 31, 0, 0, tzinfo=datetime.UTC))
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
        desc = f"{self.route} ({self.actiontype}) from: {self.originating_scram_instance}"
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

        # Unblock it
        async_to_sync(channel_layer.group_send)(
            f"translator_{self.actiontype}",
            {
                "type": "translator_remove",
                "message": {"route": str(self.route)},
            },
        )

    def get_change_reason(self):
        """Traverse some complex relationships to determine the most recent change reason.

        Returns:
           str: The most recent change reason
        """
        hist_mgr = getattr(self, self._meta.simple_history_manager_attribute)
        return hist_mgr.order_by("-history_date").first().history_change_reason


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

    hostname = models.CharField(max_length=50, unique=True)
    uuid = models.UUIDField()

    is_authorized = models.BooleanField(null=True, blank=True, default=False)
    authorized_actiontypes = models.ManyToManyField(ActionType)

    def __str__(self):
        """Only display the hostname."""
        return str(self.hostname)


channel_layer = get_channel_layer()
