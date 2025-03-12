"""Define the steps used by Behave."""

import ipaddress
import logging
import time

from behave import then, when
from behave.log_capture import capture

logging.basicConfig(level=logging.DEBUG)


@when("we add {route} with {asn}, {vrf}, and {community} to the block list")
def add_block(context, route, vrf, asn, community):
    """Block a single IP."""
    ip = ipaddress.ip_interface(route)
    event_data = {"asn": int(asn), "community": int(community)}
    context.gobgp.add_path(ip, vrf, event_data)


@then("we delete {route} with {asn}, {vrf}, and {community} from the block list")
def del_block(context, route, vrf, asn, community):
    """Remove a single IP."""
    ip = ipaddress.ip_interface(route)
    event_data = {"asn": int(asn), "community": int(community)}
    context.gobgp.del_path(ip, vrf, event_data)


def get_block_status(context, ip, vrf):
    """Check if the IP is currently blocked.

    Returns:
        bool: The return value. True if the IP is currently blocked, False otherwise.
    """
    # Allow our add/delete requests to settle
    time.sleep(1)

    ip_obj = ipaddress.ip_interface(ip)

    return context.gobgp.is_blocked(ip_obj, vrf)


@capture
@when("{route}, {vrf}, and {community} with invalid {asn} is sent")
def asn_validation_fails(context, route, vrf, asn, community):
    """Ensure the ASN was invalid."""
    add_block(context, route, vrf, asn, community)
    assert context.log_capture.find_event("ASN assertion failed")


@then("{ip} in {vrf} is blocked")
def check_block(context, ip, vrf):
    """Ensure that the IP is currently blocked."""
    assert get_block_status(context, ip, vrf)


@then("{ip} in {vrf} is unblocked")
def check_unblock(context, ip, vrf):
    """Ensure that the IP is currently unblocked."""
    assert not get_block_status(context, ip, vrf)
