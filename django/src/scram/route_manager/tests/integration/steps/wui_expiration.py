"""Define steps for WUI form tests that actually hit the running container.

Repro for https://github.com/esnet-security/SCRAM/issues/258."""

import datetime
import re

import requests
from behave import given, then, when
from django.contrib.auth import get_user_model
from django.utils import timezone

from scram.route_manager.models import Entry

WUI_URL = "http://django:8000"
WUI_USERNAME = "wui_admin"
WUI_PASSWORD = "password"  # noqa: S105 #gitleaks: allow

CSRF_RE = re.compile(r'name="csrfmiddlewaretoken" value="([^"]+)"')


@given("a superuser WUI user exists")
def create_wui_superuser(context):
    """Create an admin for the WUI."""
    user_model = get_user_model()
    user, _ = user_model.objects.get_or_create(username=WUI_USERNAME)
    user.is_staff = True
    user.is_superuser = True
    user.set_password(WUI_PASSWORD)
    user.save()


@given("we are logged in to the WUI on the primary instance")
def wui_login(context):
    """Log in over HTTP with a cookie session, exactly like a browser would."""
    session = requests.Session()
    login_url = f"{WUI_URL}/auth/login/"
    login_page = session.get(login_url, timeout=10)
    token = CSRF_RE.search(login_page.text)
    if not token:
        context.test.fail("Could not find a CSRF token on the WUI login page")
    response = session.post(
        login_url,
        data={
            "username": WUI_USERNAME,
            "password": WUI_PASSWORD,
            "csrfmiddlewaretoken": token.group(1),
        },
        timeout=10,
    )
    if response.status_code != 200 or "Logout" not in response.text:
        context.test.fail(
            f"Failed to log in to the WUI as {WUI_USERNAME}: status "
            f"{response.status_code}"
        )
    context.wui_session = session


@when(
    "we add entry {route:S} on the WUI with action type {actiontype:S} and "
    "expiration in {minutes:d} minutes entered from a browser {tz_hours:d} "
    "hours behind the server"
)
def add_entry_from_behind_browser(context, route, actiontype, minutes, tz_hours):
    """Submit the home page add form the way a browser might."""
    naive_local_now = timezone.now() - datetime.timedelta(hours=tz_hours)
    expiration = (naive_local_now + datetime.timedelta(minutes=minutes)).strftime(
        "%Y-%m-%dT%H:%M"
    )

    home = context.wui_session.get(f"{WUI_URL}/", timeout=10)
    token = CSRF_RE.search(home.text)
    if not token:
        context.test.fail("Could not find a CSRF token on the WUI home page")

    response = context.wui_session.post(
        f"{WUI_URL}/add/",
        data={
            "route": route,
            "actiontype": actiontype,
            "comment": "behave issue 258 repro",
            "expiration": expiration,
            # A fix will probably need the browser's UTC offset
            "tz_offset": str(-tz_hours * 3600),
            "csrfmiddlewaretoken": token.group(1),
        },
        timeout=10,
    )
    if response.status_code != 200 or "Entry successfully added" not in response.text:
        context.test.fail(
            f"WUI add of {route} ({actiontype}, expiration={expiration}) did not "
            f"succeed: status {response.status_code}"
        )
    context.wui_last_expiration = expiration


@then("the WUI on the primary instance shows entry {route:S}")
def wui_shows_entry(context, route):
    """Assert the entry is still listed on the WUI home page."""
    home = context.wui_session.get(f"{WUI_URL}/", timeout=10)
    if home.status_code != 200:
        context.test.fail(f"Could not load the WUI home page: {home.status_code}")
    if route not in home.text:
        entry = Entry.objects.filter(route__route=route).first()
        stored = entry.expiration if entry else "no such row"
        context.test.fail(
            f"{route} is missing from the WUI home page even though its "
            f"stored expiration ({stored}) should be in the future"
        )


@then("the entry {route:S} with action type {actiontype:S} is active in the database")
def entry_active_in_database(context, route, actiontype):
    """Assert the entry row is still active (updates deactivate)."""
    entry = (
        Entry.objects.filter(route__route=route, actiontype__name=actiontype)
        .select_related("route", "actiontype")
        .first()
    )
    if entry is None:
        context.test.fail(f"No {route} entry with action type {actiontype} exists")
    if not entry.is_active:
        context.test.fail(
            f"{route} ({actiontype}) was deactivated at its stored expiration "
            f"{entry.expiration}, but entering 'from now' times should never "
            "do that"
        )
