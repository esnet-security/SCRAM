import ipaddress
import json

from behave import then, when
from django.urls import reverse


# This does a CIDR match
@then("{route} is contained in our list of {model}s")
def step_impl(context, route, model):
    objs = context.test.client.get(reverse(f"api:v1:{model.lower()}-list"))
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
            reverse("api:v1:entry-detail", args=[ip])
        )
        context.queryException = None
    except ValueError as e:
        context.response = None
        context.queryException = e


@then("we get a ValueError")
def step_impl(context):
    assert isinstance(context.queryException, ValueError)


@then("the change entry for {value:S} is {comment}")
def step_impl(context, value, comment):
    try:
        objs = context.test.client.get(
            reverse("api:v1:entry-detail", args=[value])
        )
        context.test.assertEqual(objs.json()[0]['comment'], comment)
    except ValueError as e:
        context.response = None
        context.queryException = e
