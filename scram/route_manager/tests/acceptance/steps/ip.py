import ipaddress

from behave import then, when
from django.urls import reverse


# This does a CIDR match
@then("{route} is contained in our entrys")
def step_impl(context, route):
    objs = context.test.client.get(reverse("api:entry-list"))
    ip_target = ipaddress.ip_address(route)

    ip_found = False
    for obj in objs.json():
        net = ipaddress.ip_network(obj["route"])
        if ip_target in net:
            ip_found = True
            break

    context.test.assertTrue(ip_found)


@when("we query for {ip}")
def step_impl(context, ip):
    try:
        context.response = context.test.client.get(
            reverse("api:entry-detail", args=[ip])
        )
        context.queryException = None
    except ValueError as e:
        context.response = None
        context.queryException = e


@then("we get a ValueError")
def step_impl(context):
    assert isinstance(context.queryException, ValueError)
