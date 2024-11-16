import ipaddress
import logging
import time

from behave import then, when
from behave.log_capture import capture

logging.basicConfig(level=logging.DEBUG)


@when("we add {route} with {asn} and {community} to the block list")
def add_block(context, route, asn, community):
    ip = ipaddress.ip_interface(route)
    event_data = {"asn": int(asn), "community": int(community)}
    context.gobgp.add_path(ip, event_data)


@then("we delete {route} with {asn} and {community} from the block list")
def del_block(context, route, asn, community):
    ip = ipaddress.ip_interface(route)
    event_data = {"asn": int(asn), "community": int(community)}
    context.gobgp.del_path(ip, event_data)


def get_block_status(context, ip):
    # Allow our add/delete requests to settle
    time.sleep(1)

    ip_obj = ipaddress.ip_interface(ip)

    for path in context.gobgp.get_prefixes(ip_obj):
        if ip_obj in ipaddress.ip_network(path.destination.prefix):
            return True

    return False


@capture
@when("{route} and {community} with invalid {asn} is sent")
def asn_validation_fails(context, route, asn, community):
    add_block(context, route, asn, community)
    assert context.log_capture.find_event("ASN assertion failed")


@then("{ip} is blocked")
def check_block(context, ip):
    assert get_block_status(context, ip)


@then("{ip} is unblocked")
def check_unblock(context, ip):
    assert not get_block_status(context, ip)
