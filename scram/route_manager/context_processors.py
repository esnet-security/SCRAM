"""Define custom functions that take a request and add to the context before template rendering."""

from django.conf import settings
from django.urls import reverse


def login_logout(request):
    """Pass through the relevant URLs from the settings.

    Returns:
       dict: login and logout URLs
    """
    login_url = reverse(settings.LOGIN_URL)
    logout_url = reverse(settings.LOGOUT_URL)
    return {"login": login_url, "logout": logout_url}
