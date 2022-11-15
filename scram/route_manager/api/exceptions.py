from django.conf import settings
from rest_framework.exceptions import APIException


class PrefixTooLarge(APIException):
    v4_min_prefix = getattr(settings, "V4_MINPREFIX", 0)
    v6_min_prefix = getattr(settings, "V6_MINPREFIX", 0)
    status_code = 400
    default_detail = f"You've supplied too large of a network. settings.V4_MINPREFIX = {v4_min_prefix} settings.V6_MINPREFIX = {v6_min_prefix}"  # noqa: 501
    default_code = "prefix_too_large"


class IgnoredRoute(APIException):
    status_code = 400
    default_detail = (
        "This CIDR is on the ignore list. You are not allowed to add it here."
    )
    default_code = "ignored_route"
