from django.db import models
from netfields import InetAddressField


class IPAddress(models.Model):
    """ Our base IP model """
    ip = InetAddressField()
