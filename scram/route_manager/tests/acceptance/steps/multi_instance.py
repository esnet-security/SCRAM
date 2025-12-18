"""Define steps for multi-instance testing that actually hit both running containers."""

import datetime
import time
import urllib.parse

import requests
from behave import then, when

DJANGO_PRIMARY_URL = "http://django:8000"
DJANGO_SECONDARY_URL = "http://django-secondary:8000"


def get_auth_token(base_url: str = DJANGO_PRIMARY_URL):
    """Obtain an API authentication token for the test user."""
    response = requests.post(f"{base_url}/auth-token/", data={"username": "user", "password": "password"}, timeout=10)
    response.raise_for_status()
    return response.json()["token"]


@when("we create an entry {ip:S} on primary instance")
def create_entry_on_primary(context, ip):
    """Creates an entry via API call to the primary container."""
    try:
        response = requests.post(
            f"{DJANGO_PRIMARY_URL}/api/v1/entries/",
            json={
                "route": ip,
                "actiontype": "block",
                "comment": "behave multi-instance test",
                "who": "behave",
                "uuid": "0e7e1cbd-7d73-4968-bc4b-ce3265dc2fd3",
            },
            timeout=10,
        )
        response.raise_for_status()
        context.response = response
        context.test_ip = ip
    except requests.exceptions.RequestException as e:
        context.test.fail(f"Failed to call primary instance API: {e}")


@when("we create entry {ip:S} with {seconds:d} second expiration on primary instance")
def create_entry_with_expiration(context, ip, seconds):
    """Creates an entry with expiration via API call to the primary container."""
    td = datetime.timedelta(seconds=int(seconds))
    expiration = (datetime.datetime.now(tz=datetime.UTC) + td).isoformat()

    try:
        response = requests.post(
            f"{DJANGO_PRIMARY_URL}/api/v1/entries/",
            json={
                "route": ip,
                "actiontype": "block",
                "comment": "behave multi-instance expiration test",
                "expiration": expiration,
                "who": "behave",
                "uuid": "0e7e1cbd-7d73-4968-bc4b-ce3265dc2fd3",
            },
            timeout=10,
        )
        response.raise_for_status()
        context.response = response
        context.test_ip = ip
    except requests.exceptions.RequestException as e:
        context.test.fail(f"Failed to call primary instance API: {e}")


@when("we deactivate entry {ip:S} on primary instance")
def deactivate_entry_on_primary(context, ip):
    """Deactivates an entry via API call to the primary container."""
    if not hasattr(context, "auth_token"):
        context.auth_token = get_auth_token()

    try:
        list_response = requests.get(
            f"{DJANGO_PRIMARY_URL}/api/v1/entries/?uuid=0e7e1cbd-7d73-4968-bc4b-ce3265dc2fd3",
            headers={"Authorization": f"Token {context.auth_token}"},
            timeout=10,
        )
        list_response.raise_for_status()

        entries = list_response.json().get("results", [])
        entry_route = None
        for entry in entries:
            if entry.get("route") == ip:
                entry_route = entry["route"]
                break

        if not entry_route:
            context.test.fail(f"Entry {ip} not found in API response")

        encoded_route = urllib.parse.quote(entry_route, safe="")
        response = requests.delete(
            f"{DJANGO_PRIMARY_URL}/api/v1/entries/{encoded_route}/",
            headers={"Authorization": f"Token {context.auth_token}"},
            timeout=10,
        )
        response.raise_for_status()
        context.response = response
    except requests.exceptions.RequestException as e:
        context.test.fail(f"Failed to call primary instance API: {e}")


@when("we wait for database commit")
def wait_for_database_commit(context):
    """Wait briefly to ensure database changes are committed."""
    time.sleep(2)


@when("we wait {seconds:d} seconds for expiration")
def wait_for_expiration(context, seconds):
    """Waits for an entry to expire."""
    time.sleep(int(seconds))


@when("secondary instance runs process_updates")
def secondary_runs_process_updates(context):
    """Makes API call to secondary instance's process_updates endpoint."""
    try:
        response = requests.get(f"{DJANGO_SECONDARY_URL}/process_updates/", timeout=10)
        response.raise_for_status()
        context.secondary_response = response
        context.secondary_process_data = response.json()
    except requests.exceptions.RequestException as e:
        context.test.fail(f"Failed to call secondary instance process_updates: {e}")


@when("primary instance runs process_updates to expire entries")
def primary_runs_process_updates(context):
    """Runs process_updates on the primary instance via API."""
    try:
        response = requests.get(f"{DJANGO_PRIMARY_URL}/process_updates/", timeout=10)
        response.raise_for_status()
        context.primary_response = response
        context.primary_process_data = response.json()
    except requests.exceptions.RequestException as e:
        context.test.fail(f"Failed to call primary instance process_updates: {e}")


@then("the entry {ip:S} is inactive on secondary instance")
def check_entry_inactive_on_secondary(context, ip):
    """Checks if entry is inactive by verifying it's NOT in the active entries list."""
    if not hasattr(context, "auth_token"):
        context.auth_token = get_auth_token(DJANGO_SECONDARY_URL)

    try:
        list_response = requests.get(
            f"{DJANGO_SECONDARY_URL}/api/v1/entries/?uuid=0e7e1cbd-7d73-4968-bc4b-ce3265dc2fd3",
            headers={"Authorization": f"Token {context.auth_token}"},
            timeout=10,
        )
        list_response.raise_for_status()

        entries = list_response.json().get("results", [])
        for entry in entries:
            if entry.get("route") == ip:
                context.test.fail(f"Entry {ip} should be inactive but was found in active entries list")

        # If we get here, the entry was not found in active entries, which is correct
    except requests.exceptions.RequestException as e:
        context.test.fail(f"Failed to call API: {e}")


@then("secondary announces {ip:S} addition to block translators")
def check_announced_on_secondary(context, ip):
    """Verifies entry was processed and announced to translators."""
    if not hasattr(context, "auth_token"):
        context.auth_token = get_auth_token(DJANGO_SECONDARY_URL)

    # First verify the entry exists and is active via API
    try:
        list_response = requests.get(
            f"{DJANGO_SECONDARY_URL}/api/v1/entries/?uuid=0e7e1cbd-7d73-4968-bc4b-ce3265dc2fd3",
            headers={"Authorization": f"Token {context.auth_token}"},
            timeout=10,
        )
        list_response.raise_for_status()

        entries = list_response.json().get("results", [])
        entry_found = False
        for entry in entries:
            if entry.get("route") == ip:
                entry_found = True
                assert entry.get("is_active") is True, f"Entry {ip} should be active"
                break

        assert entry_found, f"Entry {ip} not found in API response"
    except requests.exceptions.RequestException as e:
        context.test.fail(f"Failed to call API: {e}")

    # Verify process_updates actually processed this specific entry
    if hasattr(context, "secondary_process_data"):
        reprocessed_list = context.secondary_process_data.get("entries_reprocessed_list", [])
        secondary_hostname = context.secondary_process_data.get("scram_hostname", "UNKNOWN")

        originating_instance = None
        for entry in entries:
            if entry.get("route") == ip:
                originating_instance = entry.get("originating_scram_instance", "UNKNOWN")
                break
        assert ip in reprocessed_list, (
            f"Expected {ip} in reprocessed list, got {reprocessed_list}. "
            f"Secondary hostname: {secondary_hostname}, Entry origin: {originating_instance}"
        )


@then("secondary announces {ip:S} removal to block translators")
def check_removal_announced_on_secondary(context, ip):
    """Verifies entry removal was processed and announced to translators."""
    if not hasattr(context, "auth_token"):
        context.auth_token = get_auth_token(DJANGO_SECONDARY_URL)

    # First verify the entry is NOT in the active entries list (since it was removed)
    try:
        list_response = requests.get(
            f"{DJANGO_SECONDARY_URL}/api/v1/entries/?uuid=0e7e1cbd-7d73-4968-bc4b-ce3265dc2fd3",
            headers={"Authorization": f"Token {context.auth_token}"},
            timeout=10,
        )
        list_response.raise_for_status()

        entries = list_response.json().get("results", [])
        for entry in entries:
            if entry.get("route") == ip:
                context.test.fail(f"Entry {ip} should be inactive but was found in active entries list")

        # Entry is not in active list, which is correct for a removed entry
    except requests.exceptions.RequestException as e:
        context.test.fail(f"Failed to call API: {e}")

    # Verify process_updates actually processed this specific entry
    process_data = getattr(context, "secondary_process_data", None) or getattr(context, "primary_process_data", {})
    if process_data:
        reprocessed_list = process_data.get("entries_reprocessed_list", [])
        hostname = process_data.get("scram_hostname", "UNKNOWN")
        assert ip in reprocessed_list, (
            f"Expected {ip} in reprocessed list, got {reprocessed_list}. Instance hostname: {hostname}"
        )
