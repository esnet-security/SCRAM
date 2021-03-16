from django.db import models
from django.urls import reverse

from netfields import InetAddressField
import uuid as uuid_lib


class IPAddress(models.Model):
    """ Our base IP model """
    ip = InetAddressField()
    uuid = models.UUIDField(
        db_index=True,
        default=uuid_lib.uuid4,
        editable=False)

    def get_absolute_url(self):
        return reverse('')
