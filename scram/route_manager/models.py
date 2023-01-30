import logging
import uuid as uuid_lib

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import models
from django.urls import reverse
from netfields import CidrAddressField
from simple_history.models import HistoricalRecords


class Route(models.Model):
    """Model describing a route"""

    route = CidrAddressField(unique=True)
    uuid = models.UUIDField(db_index=True, default=uuid_lib.uuid4, editable=False)

    def get_absolute_url(self):
        return reverse("")

    def __str__(self):
        return str(self.route)


class ActionType(models.Model):
    """Defines an action that can be done with a given route. e.g. Block, shunt, redirect, etc."""

    name = models.CharField(
        help_text="One-word description of the action", max_length=30
    )
    available = models.BooleanField(
        help_text="Is this a valid choice for new entries?", default=True
    )
    history = HistoricalRecords()

    def __str__(self):
        if not self.available:
            return f"{self.name} (Inactive)"
        return self.name


class Entry(models.Model):
    """An instance of an action taken on a route."""

    route = models.ForeignKey("Route", on_delete=models.PROTECT)
    actiontype = models.ForeignKey("ActionType", on_delete=models.PROTECT)
    comment = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    # TODO: fix name if this works
    history = HistoricalRecords()
    when = models.DateTimeField(auto_now_add=True)
    who = models.CharField("Username", default="Unknown", max_length=30)
    expiration = models.DateTimeField(default="9999-12-31 00:00")
    expiration_reason = models.CharField(
        help_text="Optional reason for the expiration",
        max_length=200,
        null=True,
        blank=True,
    )

    def delete(self, *args, **kwargs):
        if not self.is_active:
            # We've already expired this route, don't send another message
            return
        else:
            # We don't actually delete records; we set them to inactive and then tell the translator to remove them
            logging.info(f"Deactivating {self.route}")
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

    class Meta:
        unique_together = ["route", "actiontype"]
        verbose_name_plural = "Entries"

    def __str__(self):
        desc = f"{self.route} ({self.actiontype})"
        if not self.is_active:
            desc += " (inactive)"
        return desc

    def get_change_reason(self):
        hist_mgr = getattr(self, self._meta.simple_history_manager_attribute)
        return hist_mgr.order_by("-history_date").first().history_change_reason


class IgnoreEntry(models.Model):
    """For cidrs you NEVER want to block ie don't shoot yourself in the foot list"""

    route = CidrAddressField(unique=True)
    comment = models.CharField(max_length=100)
    history = HistoricalRecords()

    class Meta:
        verbose_name_plural = "Ignored Entries"

    def __str__(self):
        return str(self.route)


channel_layer = get_channel_layer()
