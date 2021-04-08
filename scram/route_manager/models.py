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
