import ipaddress
import time

from gobgp import GoBGP
import gobgp_pb2
from behave import then, when


@when("we add {route} to the block list")
def add_block(context, route):
    with GoBGP('gobgp:50051') as g:
        ip = ipaddress.ip_interface(route)
        g.add_block(ip)


@when("we delete {route} to the block list")
def del_block(context, route):
    with GoBGP('gobgp:50051') as g:
        ip = ipaddress.ip_interface(route)
        g.del_block(ip)


def get_block_status(context, ip):
    # Allow our add/delete requests to settle
    time.sleep(1)

    ip_obj = ipaddress.ip_address(ip)
    if ip_obj.version == 6:
        family = gobgp_pb2.Family.AFI_IP6
    else:
        family = gobgp_pb2.Family.AFI_IP

    request = gobgp_pb2.ListPathRequest(
        family=gobgp_pb2.Family(afi=family, safi=gobgp_pb2.Family.SAFI_UNICAST)
    )

    for path in context.stub.ListPath(request):
        if ip_obj in ipaddress.ip_network(path.destination.prefix):
            return True

    return False


@then("{ip} is blocked")
def check_block(context, ip):
    assert get_block_status(context, ip)


@then("{ip} is unblocked")
def check_unblock(context, ip):
    assert not get_block_status(context, ip)
