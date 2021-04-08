from behave import when, then
from django.urls import reverse
import ipaddress

# TODO: Probably want to make these generic once we have more models


@when("we add the IP {route}")
def step_impl(context, ip):
    context.response = context.test.client.post(
        reverse("route_manager:ipaddress_rest_api"), {"route": ip}
    )


@when("we remove the IP {route}")
def step_impl(context, ip):
    context.response = context.test.client.delete(
        reverse("route_manager:ipaddress_detail_rest_api", args=[ip])
    )


@when("we list the IPs")
def step_impl(context):
    context.response = context.test.client.get(
        reverse("route_manager:ipaddress_rest_api")
    )


@when("we update the IP {ip_from} to {ip_to}")
def step_impl(context, ip_from, ip_to):
    """
    :type context: behave.runner.Context
    """
    context.response = context.test.client.patch(
        reverse("route_manager:ipaddress_detail_rest_api", args=[ip_from]), {"route": ip_to}
    )


@then("the number of IPs is {num:d}")
def step_impl(context, num):
    objs = context.test.client.get(reverse("route_manager:ipaddress_rest_api"))
    context.test.assertEqual(len(objs.json()), num)


@then("{route} is one of our IPs")
def step_impl(context, ip):
    objs = context.test.client.get(reverse("route_manager:ipaddress_rest_api"))

    ip_found = False
    for obj in objs.json():
        if obj["route"] == ip:
            ip_found = True
            break

    context.test.assertTrue(ip_found)


# This does a CIDR match
@then("{route} is contained in our IPs")
def step_impl(context, ip):
    objs = context.test.client.get(reverse("route_manager:ipaddress_rest_api"))
    ip_target = ipaddress.ip_address(ip)

    ip_found = False
    for obj in objs.json():
        net = ipaddress.ip_network(obj["route"])
        if ip_target in net:
            ip_found = True
            break

    context.test.assertTrue(ip_found)
