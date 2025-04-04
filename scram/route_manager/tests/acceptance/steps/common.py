"""Define steps used exclusively by the Behave tests."""

import datetime
import time

from asgiref.sync import async_to_sync
from behave import given, step, then, when
from channels.layers import get_channel_layer
from django import conf
from django.urls import reverse

from scram.route_manager.models import ActionType, Client, WebSocketMessage, WebSocketSequenceElement


@given("a {name} actiontype is defined")
def create_actiontype(context, name):
    """Create an actiontype of that name."""
    context.channel_layer = get_channel_layer()
    async_to_sync(context.channel_layer.group_send)(
        f"translator_{name}",
        {"type": "translator_remove_all", "message": {}},
    )

    at, _ = ActionType.objects.get_or_create(name=name)
    wsm, _ = WebSocketMessage.objects.get_or_create(msg_type="translator_add", msg_data_route_field="route")
    wsm.save()
    wsse, _ = WebSocketSequenceElement.objects.get_or_create(websocketmessage=wsm, verb="A", action_type=at)
    wsse.save()


@given("a client with {name} authorization")
def create_authed_client(context, name):
    """Create a client and authorize it for that action type."""
    at, _ = ActionType.objects.get_or_create(name=name)
    authorized_client = Client.objects.create(
        hostname="authorized_client.es.net",
        uuid="0e7e1cbd-7d73-4968-bc4b-ce3265dc2fd3",
        is_authorized=True,
    )
    authorized_client.authorized_actiontypes.set([at])


@given("a client without {name} authorization")
def create_unauthed_client(context, name):
    """Create a client that has no authorized action types."""
    unauthorized_client = Client.objects.create(
        hostname="unauthorized_client.es.net",
        uuid="91e134a5-77cf-4560-9797-6bbdbffde9f8",
    )
    unauthorized_client.authorized_actiontypes.set([])


@when("we're logged in")
def login(context):
    """Login."""
    context.test.client.login(username="user", password="password")


@when("the CIDR prefix limits are {v4_minprefix:d} and {v6_minprefix:d}")
def set_cidr_limit(context, v4_minprefix, v6_minprefix):
    """Override our settings with the provided values."""
    conf.settings.V4_MINPREFIX = v4_minprefix
    conf.settings.V6_MINPREFIX = v6_minprefix


@then("we get a {status_code:d} status code")
def check_status_code(context, status_code):
    """Ensure the status code response matches the expected value."""
    context.test.assertEqual(context.response.status_code, status_code)


@when("we add the entry {value:S}")
def add_entry(context, value):
    """Block the provided route."""
    context.response = context.test.client.post(
        reverse("api:v1:entry-list"),
        {
            "route": value,
            "actiontype": "block",
            "comment": "behave",
            # Authorized uuid
            "uuid": "0e7e1cbd-7d73-4968-bc4b-ce3265dc2fd3",
            "who": "person",
        },
        format="json",
    )


@when("we add the entry {value:S} with comment {comment}")
def add_entry_with_comment(context, value, comment):
    """Block the provided route and add a comment."""
    context.response = context.test.client.post(
        reverse("api:v1:entry-list"),
        {
            "route": value,
            "actiontype": "block",
            "comment": comment,
            # Authorized uuid
            "uuid": "0e7e1cbd-7d73-4968-bc4b-ce3265dc2fd3",
            "who": "person",
        },
    )


@when("we add the entry {value:S} with expiration {exp:S}")
def add_entry_with_absolute_expiration(context, value, exp):
    """Block the provided route and add an absolute expiration datetime."""
    context.response = context.test.client.post(
        reverse("api:v1:entry-list"),
        {
            "route": value,
            "actiontype": "block",
            "comment": "test",
            "expiration": exp,
            # Authorized uuid
            "uuid": "0e7e1cbd-7d73-4968-bc4b-ce3265dc2fd3",
            "who": "person",
        },
    )


@when("we add the entry {value:S} with expiration in {secs:d} seconds")
def add_entry_with_relative_expiration(context, value, secs):
    """Block the provided route and add a relative expiration."""
    td = datetime.timedelta(seconds=secs)
    expiration = datetime.datetime.now(tz=datetime.UTC) + td

    context.response = context.test.client.post(
        reverse("api:v1:entry-list"),
        {
            "route": value,
            "actiontype": "block",
            "comment": "test",
            "expiration": expiration,
            # Authorized uuid
            "uuid": "0e7e1cbd-7d73-4968-bc4b-ce3265dc2fd3",
            "who": "person",
        },
    )


@step("we wait {secs:d} seconds")
def wait(context, secs):
    """Wait to allow messages to propagate."""
    time.sleep(secs)


@then("we remove expired entries")
def remove_expired(context):
    """Call the function that removes expired entries."""
    context.response = context.test.client.get(reverse("route_manager:process-updates"))


@when("we add the ignore entry {value:S}")
def add_ignore_entry(context, value):
    """Add an IgnoreEntry with the specified route."""
    context.response = context.test.client.post(
        reverse("api:v1:ignoreentry-list"),
        {"route": value, "comment": "test api"},
    )


@when("we remove the {model} {value}")
def remove_an_object(context, model, value):
    """Remove any model object with the matching value."""
    context.response = context.test.client.delete(reverse(f"api:v1:{model.lower()}-detail", args=[value]))


@when("we list the {model}s")
def list_objects(context, model):
    """List all objects of an arbitrary model."""
    context.response = context.test.client.get(reverse(f"api:v1:{model.lower()}-list"))


@when("we update the {model} {value_from} to {value_to}")
def update_object(context, model, value_from, value_to):
    """Modify any model object with the matching value to the new value instead."""
    context.response = context.test.client.patch(
        reverse(f"api:v1:{model.lower()}-detail", args=[value_from]),
        {model.lower(): value_to},
    )


@then("the number of {model}s is {num:d}")
def count_objects(context, model, num):
    """Count the number of objects of an arbitrary model."""
    objs = context.test.client.get(reverse(f"api:v1:{model.lower()}-list"))
    context.test.assertEqual(len(objs.json()["results"]), num)


model_to_field_mapping = {"entry": "route"}


@then("{value} is one of our list of {model}s")
def check_object(context, value, model):
    """Ensure that the arbitrary model has an object with the specified value."""
    objs = context.test.client.get(reverse(f"api:v1:{model.lower()}-list"))

    found = False
    for obj in objs.json()["results"]:
        # For some models, we need to look at a different field.
        model = model_to_field_mapping.get(model.lower(), model.lower())
        if obj[model].lower() == value.lower():
            found = True
            break

    context.test.assertTrue(found)


@when("we register a client named {hostname} with the uuid of {uuid}")
def add_client(context, hostname, uuid):
    """Create a client with a specific UUID."""
    context.response = context.test.client.post(
        reverse("api:v1:client-list"),
        {
            "hostname": hostname,
            "uuid": uuid,
        },
    )
