from django.db import models
from django.urls import reverse

from netfields import InetAddressField
import uuid as uuid_lib


class Route(models.Model):
    """ Model describing a route """
    route = InetAddressField(unique=True)
    uuid = models.UUIDField(
        db_index=True,
        default=uuid_lib.uuid4,
        editable=False)

    def get_absolute_url(self):
        return reverse('')


class ActionType(models.Model):
    """Defines an action that can be done with a given route. e.g. Block, shunt, redirect."""
    name = models.CharField("One-word description of the action", max_length=30)
    available = models.BooleanField("Is this a valid choice for new entries?", default=True)
