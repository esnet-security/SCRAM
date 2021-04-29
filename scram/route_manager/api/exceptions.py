from rest_framework.exceptions import APIException


class PrefixTooLarge(APIException):
    status_code = 400
    default_detail = "You've supplied too large of a network. Defaults: v4 >= 8 v6 >=32"
    default_code = "prefix_too_large"
