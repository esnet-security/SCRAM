"""Define the configuration scheme using environ-config."""

import environ
from attrs.validators import in_


@environ.config(prefix="SCRAM")
class AppConfig:
    """Top level configuration (i.e. SCRAM_)."""

    debugger = environ.var(
        default="",
        help='Debug SCRAM with a debugger. Set to either "pycharm-pydevd" or "debugpy".',
        validator=in_(["pycharm-pydevd", "debugpy", ""]),
    )


cfg = environ.to_config(AppConfig)
