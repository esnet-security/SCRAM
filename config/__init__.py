"""Define the configuration scheme using environ-config."""

import logging

import environ
from attrs.validators import in_

logger = logging.getLogger(__name__)


@environ.config(prefix="SCRAM")
class AppConfig:
    """Top level configuration (i.e. SCRAM_)."""

    debugger = environ.var(
        default="",
        help='Will launch the appropriate debugger if set to either "pycharm-pydevd" or "debugpy".')
    
    @debugger.validator
    def _warn_on_unknown_debugger(self, var, debugger):
        if debugger and debugger not in {"pycharm-pydevd", "debugpy"}:
            logger.warning("Unknown debugger value: %s", debugger)


cfg = environ.to_config(AppConfig)
