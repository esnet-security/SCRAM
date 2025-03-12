"""Define steps used for syncing-related logic by the Behave tests."""

from behave import step, then, when
from django.conf import settings
from django.urls import reverse

from scram.route_manager.models import ActionType, Entry, Route


@step("an entry {ip} from scram instance {instance_name} is added to the database")
def add_entry_with_instance_name(context, ip, instance_name):
    """Creates an entry in the database with the specified data and originating instance."""
    if instance_name == "current":
        instance_name = settings.SCRAM_HOSTNAME

    route = Route(route=ip)
    route.save()
    at = ActionType.objects.get(pk=1)

    entry_data = {
        "route": route,
        "is_active": True,
        "actiontype": at,
        "comment": "behave sync blocking",
        "who": "behave",
        "originating_scram_instance": instance_name,
    }

    entry = Entry(**entry_data)
    entry.save()
    context.entry = entry


@when("process_updates is run")
def run_process_updates(context):
    """Runs the process_updates view."""
    context.response = context.test.client.get(reverse("route_manager:process-updates"))


@then("the entry {ip} should not be announced again")
def check_not_announced(context, ip):
    """Checks if the entry has not been re-announced because this instance originally announced it."""
    testing_hostname = settings.SCRAM_HOSTNAME

    try:
        entry = Entry.objects.get(route__route=ip, originating_scram_instance=testing_hostname)
    except Entry.DoesNotExist:
        return

    assert entry.is_active is False, f"Entry {ip} was unexpectedly announced"
