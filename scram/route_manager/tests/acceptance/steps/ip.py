import ipaddress

from behave import then
from django.urls import reverse


# This does a CIDR match
@then("{route} is contained in our entrys")
def step_impl(context, route):
    objs = context.test.client.get(reverse("api:entry-list"))
    ip_target = ipaddress.ip_address(route)

    ip_found = False
    for obj in objs.json():
        # Duplicated ["route"] to traverse the foreignkey relationship
        net = ipaddress.ip_network(obj["route"]["route"])
        if ip_target in net:
            ip_found = True
            break

    context.test.assertTrue(ip_found)
