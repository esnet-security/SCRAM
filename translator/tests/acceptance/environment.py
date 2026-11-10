"""Configure the test environment before executing acceptance tests."""

import logging

from api import common_pb2, gobgp_pb2
from translator.gobgp import GoBGP

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 10

_FLOW_SPEC_AFIS = (common_pb2.Family.AFI_IP, common_pb2.Family.AFI_IP6)


def before_all(context):
    """Create a GoBGP object."""
    context.gobgp = GoBGP("gobgp:50051")
    context.flowspec_rules = []
    context.config.setup_logging()


def before_scenario(context, scenario):
    """Start every scenario with an empty list of FlowSpec rules to clean up."""
    context.flowspec_rules = []


def after_scenario(context, scenario):
    """Delete the FlowSpec rules the scenario added, then sweep the FlowSpec RIB.

    gobgp.py's del_all_paths() only withdraws unicast routes, and del_flowspec() refuses to delete
    rules its own NLRI comparison cannot match (pinned by several flowspec.feature scenarios), so
    the sweep sends a raw family-wide DeletePath per address family. It is idempotent, only ever
    targets SAFI_FLOW_SPEC_UNICAST, and is what keeps scenarios independent of each other.
    """
    for source, destination, data in context.flowspec_rules:
        try:
            context.gobgp.del_flowspec(source, destination, data)
        except Exception:  # cleanup must never mask the scenario's own result
            logger.exception("FlowSpec cleanup failed for rule: %s", data)
    context.flowspec_rules = []
    for afi in _FLOW_SPEC_AFIS:
        try:
            context.gobgp.stub.DeletePath(
                gobgp_pb2.DeletePathRequest(
                    table_type=gobgp_pb2.TABLE_TYPE_GLOBAL,
                    family=common_pb2.Family(afi=afi, safi=common_pb2.Family.SAFI_FLOW_SPEC_UNICAST),
                ),
                _TIMEOUT_SECONDS,
            )
        except Exception:  # a failed sweep surfaces in the clean_slate guard scenarios
            logger.exception("FlowSpec RIB sweep failed")
