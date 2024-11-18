"""Configure the test environment before executing acceptance tests."""

from gobgp import GoBGP


def before_all(context):
    """Create a GoBGP object."""
    context.gobgp = GoBGP("gobgp:50051")
    context.config.setup_logging()
