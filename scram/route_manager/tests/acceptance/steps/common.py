import datetime
import time

import django.conf as conf
from asgiref.sync import async_to_sync
from behave import given, step, then, when
from channels.layers import get_channel_layer
from django.urls import reverse

from scram.route_manager.models import ActionType, Client, WebSocketMessage, WebSocketSequenceElement


@given("a {name} actiontype is defined")
def define_block(context, name):
    context.channel_layer = get_channel_layer()
    async_to_sync(context.channel_layer.group_send)(
        f"translator_{name}", {"type": "translator_remove_all", "message": {}}
    )

    at, created = ActionType.objects.get_or_create(name=name)
    wsm, created = WebSocketMessage.objects.get_or_create(msg_type="translator_add", msg_data_route_field="route")
    wsm.save()
    wsse, created = WebSocketSequenceElement.objects.get_or_create(websocketmessage=wsm, verb="A", action_type=at)
    wsse.save()


@given("a client with {name} authorization")
def define_block(context, name):
    at, created = ActionType.objects.get_or_create(name=name)
    authorized_client = Client.objects.create(
        hostname="authorized_client.es.net",
        uuid="0e7e1cbd-7d73-4968-bc4b-ce3265dc2fd3",
        is_authorized=True,
    )
    authorized_client.authorized_actiontypes.set([at])


@given("a client without {name} authorization")
def define_block(context, name):
    unauthorized_client = Client.objects.create(
        hostname="unauthorized_client.es.net",
        uuid="91e134a5-77cf-4560-9797-6bbdbffde9f8",
    )
    unauthorized_client.authorized_actiontypes.set([])


@when("we're logged in")
def step_impl(context):
    context.test.client.login(username="user", password="password")


@when("the CIDR prefix limits are {v4_minprefix:d} and {v6_minprefix:d}")
def step_impl(context, v4_minprefix, v6_minprefix):
    conf.settings.V4_MINPREFIX = v4_minprefix
    conf.settings.V6_MINPREFIX = v6_minprefix


@then("we get a {status_code:d} status code")
def step_impl(context, status_code):
    context.test.assertEqual(context.response.status_code, status_code)


@when("we add the entry {value:S}")
def step_impl(context, value):
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
def step_impl(context, value, comment):
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
def step_impl(context, value, exp):
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
def step_impl(context, value, secs):
    td = datetime.timedelta(seconds=secs)
    expiration = datetime.datetime.now() + td

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
def step_impl(context, secs):
    time.sleep(secs)


@then("we remove expired entries")
def step_impl(context):
    context.response = context.test.client.get(reverse("route_manager:process-expired"))


@when("we add the ignore entry {value:S}")
def step_impl(context, value):
    context.response = context.test.client.post(
        reverse("api:v1:ignoreentry-list"), {"route": value, "comment": "test api"}
    )


@when("we remove the {model} {value}")
def step_impl(context, model, value):
    context.response = context.test.client.delete(reverse(f"api:v1:{model.lower()}-detail", args=[value]))


@when("we list the {model}s")
def step_impl(context, model):
    context.response = context.test.client.get(reverse(f"api:v1:{model.lower()}-list"))


@when("we update the {model} {value_from} to {value_to}")
def step_impl(context, model, value_from, value_to):
    context.response = context.test.client.patch(
        reverse(f"api:v1:{model.lower()}-detail", args=[value_from]),
        {model.lower(): value_to},
    )


@then("the number of {model}s is {num:d}")
def step_impl(context, model, num):
    objs = context.test.client.get(reverse(f"api:v1:{model.lower()}-list"))
    context.test.assertEqual(len(objs.json()), num)


model_to_field_mapping = {"entry": "route"}


@then("{value} is one of our list of {model}s")
def step_impl(context, value, model):
    objs = context.test.client.get(reverse(f"api:v1:{model.lower()}-list"))

    found = False
    for obj in objs.json():
        # For some models, we need to look at a different field.
        model = model_to_field_mapping.get(model.lower(), model.lower())
        if obj[model].lower() == value.lower():
            found = True
            break

    context.test.assertTrue(found)


@when("we register a client named {hostname} with the uuid of {uuid}")
def step_impl(context, hostname, uuid):
    context.response = context.test.client.post(
        reverse("api:v1:client-list"),
        {
            "hostname": hostname,
            "uuid": uuid,
        },
    )
