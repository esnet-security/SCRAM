from behave import given, then, when
from django.urls import reverse

from scram.route_manager.models import ActionType


@given("a {name} actiontype is defined")
def define_block(context, name):
    at, created = ActionType.objects.get_or_create(name=name)


@when("we're logged in")
def step_impl(context):
    context.test.client.login(username="user", password="password")


@then("we get a {status_code:d} status code")
def step_impl(context, status_code):
    context.test.assertEqual(context.response.status_code, status_code)


@when("we add the entry {value}")
def step_impl(context, value):
    context.response = context.test.client.post(
        reverse("api:entry-list"), {"route": value, "actiontype": "block"}
    )


# @when("we add the {model} {value}")
# def step_impl(context, model, value):
#     context.response = context.test.client.post(
#         reverse(f"api:{model.lower()}-list"), {model.lower(): value, "actiontype": 1}
#     )


@when("we remove the {model} {value}")
def step_impl(context, model, value):
    context.response = context.test.client.delete(
        reverse(f"api:{model.lower()}-detail", args=[value])
    )


@when("we list the {model}s")
def step_impl(context, model):
    context.response = context.test.client.get(reverse(f"api:{model.lower()}-list"))


@when("we update the {model} {value_from} to {value_to}")
def step_impl(context, model, value_from, value_to):
    """
    :type context: behave.runner.Context
    """
    context.response = context.test.client.patch(
        reverse(f"api:{model.lower()}-detail", args=[value_from]),
        {model.lower(): value_to},
    )


@then("the number of {model}s is {num:d}")
def step_impl(context, model, num):
    objs = context.test.client.get(reverse(f"api:{model.lower()}-list"))
    context.test.assertEqual(len(objs.json()), num)


@then("{value} is one of our list of {model}s")
def step_impl(context, value, model):
    objs = context.test.client.get(reverse(f"api:{model.lower()}-list"))

    found = False
    for obj in objs.json():
        if obj[model.lower()] == value:
            found = True
            break

    context.test.assertTrue(found)
