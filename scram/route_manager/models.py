import uuid as uuid_lib

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import models
from django.urls import reverse
from netfields import CidrAddressField


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

    def __str__(self):
        if not self.available:
            return f"{self.name} (Inactive)"
        return self.name


class Entry(models.Model):
    """An instance of an action taken on a route."""

    route = models.ForeignKey("Route", on_delete=models.PROTECT)
    actiontype = models.ForeignKey("ActionType", on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)

    def delete(self, *args, **kwargs):
        if not self.is_active:
            # We've already expired this route, don't send another message
            return

        # Expire ALL history objects for this route
        for h in self.history_set.all():
            h.delete()

    class Meta:
        unique_together = ["route", "actiontype"]
        verbose_name_plural = 'Entries'

    def __str__(self):
        desc = f"{self.route} ({self.actiontype})"
        if not self.is_active:
            desc += " (inactive)"
        return desc


class IgnoreEntry(models.Model):
    """For cidrs you NEVER want to block ie don't shoot yourself in the foot list"""
    route = CidrAddressField(unique=True)
    comment = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = 'Ignored Entries'

    def __str__(self):
        return str(self.route)


channel_layer = get_channel_layer()


class History(models.Model):
    """Who, what, when, why"""

    entry = models.ForeignKey("Entry", on_delete=models.CASCADE)

    why = models.CharField("Comment for the action", max_length=200)
    when = models.DateTimeField(auto_now_add=True)
    who = models.CharField("Username", default="Unknown", max_length=30)
    expiration = models.DateTimeField(default="9999-12-31 00:00")
    expiration_reason = models.CharField(
        help_text="Optional reason for the expiration",
        max_length=200,
        null=True,
        blank=True,
    )

    remove_why = models.CharField("Comment for the removal action", max_length=200, null=True, blank=True)
    remove_when = models.DateTimeField("When did it get removed", null=True, blank=True)
    remove_who = models.CharField("Username for the removal", max_length=30, null=True, blank=True)

    is_active = models.BooleanField(default=True)

    def delete(self, *args, **kwargs):
        self.is_active = False
        self.save()

        # We have no other active History objects pointing to the same object
        if self.entry.is_active and \
            not History.objects.filter(entry=self.entry_id,
                                       is_active=True).count():

            self.entry.is_active = False
            self.entry.save()

            # Unblock it
            async_to_sync(channel_layer.group_send)(
                f"translator_{self.entry.actiontype}",
                {"type": f"remove_{self.entry.actiontype}",
                 "message": {"route": str(self.entry.route)}},
            )

    class Meta:
        verbose_name_plural = 'Histories'

    def __str__(self):
        desc = f"{self.entry.route}: {self.why}"
        if not self.entry.is_active:
            desc += " (inactive)"
        return desc
