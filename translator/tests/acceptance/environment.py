"""Configure the test environment before executing acceptance tests."""

from gobgp import GoBGP

from translator import GOBGP_URL, REDIS_DB_INDEX, REDIS_PORT, REDIS_URL


def before_all(context):
    """Create a GoBGP object."""
    context.gobgp = GoBGP(GOBGP_URL, REDIS_URL, REDIS_PORT, REDIS_DB_INDEX)
    context.config.setup_logging()
