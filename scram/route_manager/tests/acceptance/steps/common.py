from behave import then, when

from django.urls import reverse


@when("we're logged in")
def step_impl(context):
    context.test.client.login(username="user", password="password")


@then("we get a {status_code:d} status code")
def step_impl(context, status_code):
    context.test.assertEqual(context.response.status_code, status_code)


@when("we list the actiontypes")
def step_impl(context):
    context.response = context.test.client.get(
        reverse("api:actiontype-list")
    )


@then("the number of actiontypes is {num:d}")
def step_impl(context, num):
    objs = context.test.client.get(reverse("api:actiontype-list"))
    context.test.assertEqual(len(objs.json()), num)
