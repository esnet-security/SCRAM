"""Register ourselves with Django."""

import logging

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class UsersConfig(AppConfig):
    """Define the name of the module for the Users app."""

    name = "scram.users"
    verbose_name = _("Users")

    @staticmethod
    def ready():
        """Check if signals are registered for User events."""
        try:
            import scram.users.signals  # noqa F401
        except ImportError:
            logger.warning("SCRAM user signals not found")
