"""Define the steps used by Behave."""

import ipaddress
import logging
import time

from behave import then, when
from behave.log_capture import capture

logging.basicConfig(level=logging.DEBUG)


@when("we add {route} with {asn} and {community} to the block list")
def add_block(context, route, asn, community):
    """Block a single IP."""
    ip = ipaddress.ip_interface(route)
    event_data = {"asn": int(asn), "community": int(community)}
    context.gobgp.add_path(ip, event_data)


@then("we delete {route} with {asn} and {community} from the block list")
def del_block(context, route, asn, community):
    """Remove a single IP."""
    ip = ipaddress.ip_interface(route)
    event_data = {"asn": int(asn), "community": int(community)}
    context.gobgp.del_path(ip, event_data)


def get_block_status(context, ip):
    """Check if the IP is currently blocked."""
    # Allow our add/delete requests to settle
    time.sleep(1)

    ip_obj = ipaddress.ip_interface(ip)

    return any(ip_obj in ipaddress.ip_network(path.destination.prefix) for path in context.gobgp.get_prefixes(ip_obj))


@capture
@when("{route} and {community} with invalid {asn} is sent")
def asn_validation_fails(context, route, asn, community):
    """Ensure the ASN was invalid."""
    add_block(context, route, asn, community)
    assert context.log_capture.find_event("ASN assertion failed")


@then("{ip} is blocked")
def check_block(context, ip):
    """Ensure that the IP is currently blocked."""
    assert get_block_status(context, ip)


@then("{ip} is unblocked")
def check_unblock(context, ip):
    """Ensure that the IP is currently unblocked."""
    assert not get_block_status(context, ip)
