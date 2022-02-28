from django.conf import settings
from rest_framework.exceptions import APIException


class PrefixTooLarge(APIException):
    v4_min_prefix = getattr(settings, f"V4_MINPREFIX", 0)
    v6_min_prefix = getattr(settings, f"V6_MINPREFIX", 0)
    status_code = 400
    default_detail = f"You've supplied too large of a network. v4 max >= {v4_min_prefix} v6 >= {v6_min_prefix}"
    default_code = "prefix_too_large"
