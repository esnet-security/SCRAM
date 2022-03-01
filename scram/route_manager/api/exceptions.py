from django.conf import settings
from rest_framework.exceptions import APIException


class PrefixTooLarge(APIException):
    v4_min_prefix = getattr(settings, "V4_MINPREFIX", 0)
    v6_min_prefix = getattr(settings, "V6_MINPREFIX", 0)
    status_code = 400
    default_detail = f"You've supplied too large of a network based. settings.V4_MINPREFIX = {v4_min_prefix} settings.V6_MINPREFIX= {v6_min_prefix}"
    default_code = "prefix_too_large"
