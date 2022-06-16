from behave import given, then, when
import django.conf as conf
from django.urls import reverse

from scram.route_manager.models import ActionType


@given("a {name} actiontype is defined")
def define_block(context, name):
    at, created = ActionType.objects.get_or_create(name=name)


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


@when("we add the entry {value}")
def step_impl(context, value):
    context.response = context.test.client.post(
        reverse("api:v1:entry-list"), {"route": value, "actiontype": "block"}
    )


@when("we remove the {model} {value}")
def step_impl(context, model, value):
    context.response = context.test.client.delete(
        reverse(f"api:v1:{model.lower()}-detail", args=[value])
    )


@when("we list the {model}s")
def step_impl(context, model):
    context.response = context.test.client.get(reverse(f"api:v1:{model.lower()}-list"))


@when("we update the {model} {value_from} to {value_to}")
def step_impl(context, model, value_from, value_to):
    """
    :type context: behave.runner.Context
    """
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
        if obj[model] == value:
            found = True
            break

    context.test.assertTrue(found)
