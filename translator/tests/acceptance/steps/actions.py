import ipaddress
import time

from behave import then, when


@when("we add {route} with {asn} and {community} to the block list")
def add_block(context, route, asn, community):
    ip = ipaddress.ip_interface(route)
    event_data = {"asn": int(asn), "community": int(community)}
    context.gobgp.add_path(ip, event_data)


@when("we delete {route} from the block list")
def del_block(context, route):
    ip = ipaddress.ip_interface(route)
    event_data = {"asn": 64500, "community": 666}
    context.gobgp.del_path(ip, event_data)


def get_block_status(context, ip):
    # Allow our add/delete requests to settle
    time.sleep(1)

    ip_obj = ipaddress.ip_interface(ip)

    for path in context.gobgp.get_prefixes(ip_obj):
        if ip_obj in ipaddress.ip_network(path.destination.prefix):
            return True

    return False


@then("{ip} is blocked")
def check_block(context, ip):
    assert get_block_status(context, ip)


@then("{ip} is unblocked")
def check_unblock(context, ip):
    assert not get_block_status(context, ip)
