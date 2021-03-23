from behave import when, then
from django.urls import reverse
import ipaddress

# TODO: Probably want to make these generic once we have more models


@when("we add the IP {ip}")
def step_impl(context, ip):
    context.response = context.test.client.post(
        reverse("route_manager:ipaddress_rest_api"), {"ip": ip}
    )


@when("we remove the IP {ip}")
def step_impl(context, ip):
    context.response = context.test.client.delete(
        reverse("route_manager:ipaddress_detail_rest_api", args=[ip])
    )


@when("we list the IPs")
def step_impl(context):
    context.response = context.test.client.get(
        reverse("route_manager:ipaddress_rest_api")
    )


@then("the number of IPs is {num:d}")
def step_impl(context, num):
    objs = context.test.client.get(reverse("route_manager:ipaddress_rest_api"))
    context.test.assertEqual(len(objs.json()), num)


@then("{ip} is one of our IPs")
def step_impl(context, ip):
    objs = context.test.client.get(reverse("route_manager:ipaddress_rest_api"))

    ip_found = False
    for obj in objs.json():
        if obj["ip"] == ip:
            ip_found = True
            break

    context.test.assertTrue(ip_found)


# This does a CIDR match
@then("{ip} is contained in our IPs")
def step_impl(context, ip):
    objs = context.test.client.get(reverse("route_manager:ipaddress_rest_api"))
    ip_target = ipaddress.ip_address(ip)

    ip_found = False
    for obj in objs.json():
        net = ipaddress.ip_network(obj["ip"])
        if ip_target in net:
            ip_found = True
            break

    context.test.assertTrue(ip_found)
