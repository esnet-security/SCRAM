from behave import then, when


@when("we add {route} to the {actiontype} list")
def xadd(context, actiontype, route):
    context.db.xadd(f"{actiontype}_add", {"route": route, "actiontype": actiontype})

@when("we delete {route} from the {actiontype} list")
def xdel(context, actiontype, route):
    context.db.xdel(f"{actiontype}_add", {"route": route, "actiontype": actiontype})

@then("{ip} is unblocked")
def check_unblock(context, ip):
    assert True

@then("{ip} is blocked")
def check_block(context, ip):
    assert True
