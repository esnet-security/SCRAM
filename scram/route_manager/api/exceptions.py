"""Custom exceptions for the API."""

from django.conf import settings
from rest_framework.exceptions import APIException


class PrefixTooLarge(APIException):
    """The CIDR prefix that was specified is larger than 32 bits for IPv4 of 128 bits for IPv6."""

    v4_min_prefix = getattr(settings, "V4_MINPREFIX", 0)
    v6_min_prefix = getattr(settings, "V6_MINPREFIX", 0)
    status_code = 400
    default_detail = f"You've supplied too large of a network. settings.V4_MINPREFIX = {v4_min_prefix} settings.V6_MINPREFIX = {v6_min_prefix}"  # noqa: 501
    default_code = "prefix_too_large"


class IgnoredRoute(APIException):
    """An operation attempted to add a route that overlaps with a route on the ignore list."""

    status_code = 400
    default_detail = "This CIDR is on the ignore list. You are not allowed to add it here."
    default_code = "ignored_route"


class ActiontypeNotAllowed(APIException):
    """An operation attempted to perform an action on behalf of a client that is unauthorized to perform that type."""

    status_code = 403
    default_detail = "This client is not allowed to use this actiontype"
    default_code = "actiontype_not_allowed"
