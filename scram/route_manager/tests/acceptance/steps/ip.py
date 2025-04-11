"""Define steps used for IP-related logic by the Behave tests."""

import ipaddress

from behave import then, when
from django.urls import reverse


@then("{route} is contained in our list of {model}s")
def check_route(context, route, model):
    """Perform a CIDR match on the matching object."""
    objs = context.test.client.get(reverse(f"api:v1:{model.lower()}-list"))
    ip_target = ipaddress.ip_address(route)

    ip_found = False
    for obj in objs.json()["results"]:
        net = ipaddress.ip_network(obj["route"])
        if ip_target in net:
            ip_found = True
            break

    context.test.assertTrue(ip_found)


@when("we query for {ip}")
def check_ip(context, ip):
    """Find an Entry for the specified IP."""
    try:
        context.response = context.test.client.get(reverse("api:v1:entry-detail", args=[ip]))
        context.queryException = None
    except ValueError as e:
        context.response = None
        context.queryException = e


@then("we get a ValueError")
def check_error(context):
    """Ensure we received a ValueError exception."""
    assert isinstance(context.queryException, ValueError)


@then("the change entry for {value:S} is {comment}")
def check_comment(context, value, comment):
    """Verify the comment for the Entry."""
    try:
        objs = context.test.client.get(reverse("api:v1:entry-detail", args=[value]))
        context.test.assertEqual(objs.json()[0]["comment"], comment)
    except ValueError as e:
        context.response = None
        context.queryException = e
