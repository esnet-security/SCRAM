"""Define steps used for IP-related logic by the Behave tests."""

import ipaddress
import json

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
        context.response = context.test.client.get(
            reverse("api:v1:entry-detail", args=[ip])
        )
        context.queryException = None
    except ValueError as e:
        context.response = None
        context.queryException = e


@then("we get a ValueError")
def check_error(context):
    """Ensure we received a ValueError exception."""
    assert isinstance(context.queryException, ValueError)


@then("the comment for entry {value:S} is {comment}")
def check_comment(context, value, comment):
    """Verify the comment for the Entry."""
    try:
        objs = context.test.client.get(reverse("api:v1:entry-detail", args=[value]))
        context.test.assertEqual(objs.json()["comment"], comment)
    except ValueError as e:
        context.response = None
        context.queryException = e


@then("we update the entry {value:S} with comment {comment}")
def update_entry_comment(context, value, comment):
    """Update the entry with a new comment."""
    data = {"comment": comment, "who": context.client.client_name}

    context.response = context.test.client.put(
        reverse("api:v1:entry-detail", args=[value]),
        data=json.dumps(data),
        content_type="application/json",
    )


@then("the entry {value:S} comment is {comment}")
def check_entry_comment_not_equal(context, value, comment):
    """Verify the comment was updated."""
    objs = context.test.client.get(reverse("api:v1:entry-detail", args=[value]))
    context.test.assertEqual(objs.json()["comment"], comment)


@when("we search for {ip}")
def search_ip(context, ip):
    """Search our main search bar for an IP."""
    client = context.test.web_client
    search_url = reverse("route_manager:search")

    context.response = client.post(search_url, data={"cidr": ip})
