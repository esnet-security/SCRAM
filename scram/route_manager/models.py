import uuid as uuid_lib

from django.db import models
from django.urls import reverse
from netfields import CidrAddressField


class Route(models.Model):
    """ Model describing a route """

    route = CidrAddressField(unique=True)
    uuid = models.UUIDField(db_index=True, default=uuid_lib.uuid4, editable=False)

    def get_absolute_url(self):
        return reverse("")

    def __str__(self):
        return str(self.route)


class ActionType(models.Model):
    """ Defines an action that can be done with a given route. e.g. Block, shunt, redirect, etc. """

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
    """ An instance of an action taken on a route. """

    route = models.ForeignKey("Route", on_delete=models.PROTECT)
    actiontype = models.ForeignKey("ActionType", on_delete=models.PROTECT)

    class Meta:
        unique_together = ["route", "actiontype"]


class History(models.Model):
    """ Who, what, when, why """

    entry = models.ForeignKey("Entry", on_delete=models.CASCADE)
    who = models.CharField("Username", default="Unknown", max_length=30)
    why = models.CharField("Comment for the action", max_length=200)
    when = models.DateTimeField(auto_now_add=True)

    expiration = models.DateTimeField(default="9999, 12, 31, tz=timezone.utc")
    expiration_reason = models.CharField(
        help_text="Optional reason for the expiration",
        max_length=200,
        null=True,
        blank=True,
    )
