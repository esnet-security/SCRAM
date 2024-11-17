"""Define custom functions that take a request and add to the context before template rendering."""

from django.conf import settings


def settings_context(_request):
    """Define settings available by default to the templates context."""
    # Note: we intentionally do NOT expose the entire settings
    # to prevent accidental leaking of sensitive information
    return {"DEBUG": settings.DEBUG}
