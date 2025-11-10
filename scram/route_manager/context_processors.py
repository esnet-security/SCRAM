"""Define custom functions that take a request and add to the context before template rendering."""

from django.conf import settings
from django.urls import reverse

from scram.route_manager.models import Entry


def login_logout(request):
    """Pass through the relevant URLs from the settings.

    Returns:
       dict: login and logout URLs
    """
    login_url = reverse(settings.LOGIN_URL)
    logout_url = reverse(settings.LOGOUT_URL)

    return {"login": login_url, "logout": logout_url}


def active_count(request):
    """Grab the active count of blocks.

    Returns:
        dict: active count of blocks
    """
    if "admin" not in request.META["PATH_INFO"]:
        active_block_entries = Entry.objects.filter(is_active=True).count()
        total_block_entries = Entry.objects.all().count()
        return {"active_block_entries": active_block_entries, "total_block_entries": total_block_entries}
    return {}
