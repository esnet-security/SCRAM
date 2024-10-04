import logging

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class UsersConfig(AppConfig):
    name = "scram.users"
    verbose_name = _("Users")

#    def ready(self):
#        try:
#            import scram.users.signals  # noqa F401
#        except ImportError:
#            logger.warning("SCRAM user signals not found")
