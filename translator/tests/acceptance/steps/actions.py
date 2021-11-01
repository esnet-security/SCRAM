import ipaddress
import time

import gobgp_pb2
from behave import then, when


@when("we add {route} to the {actiontype} list")
def xadd(context, actiontype, route):
    context.db.xadd(f"{actiontype}_add", {"route": route, "actiontype": actiontype})


@when("we delete {route} from the {actiontype} list")
def xdel(context, actiontype, route):
    context.db.xdel(f"{actiontype}_add", {"route": route, "actiontype": actiontype})


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
