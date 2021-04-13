from behave import then, when


@when("we're logged in")
def step_impl(context):
    context.test.client.login(username="user", password="password")


@then("we get a {status_code:d} status code")
def step_impl(context, status_code):
    context.test.assertEqual(context.response.status_code, status_code)
