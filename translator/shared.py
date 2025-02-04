"""Provide a location for code that we want to share between all translators."""

import logging
from ipaddress import IPv4Interface, IPv6Interface, ip_interface

from exceptions import ASNError

MAX_ASN_VAL = 2**32 - 1

logger = logging.getLogger(__name__)


def asn_is_valid(asn: int) -> bool:
    """asn_is_valid makes sure that an ASN passed in is a valid 2 or 4 Byte ASN.

    Args:
        asn (int): The Autonomous System Number that we want to validate

    Raises:
        ASNError: If the ASN is not between 0 and 4294967295 or is not an integer.

    Returns:
        bool: True if the ASN is valid, False if it's Invalid.

    """
    if not isinstance(asn, int):
        msg = f"ASN {asn} is not an Integer, has type {type(asn)}"
        raise ASNError(msg)
    if not 0 < asn < MAX_ASN_VAL:
        # This is the max as stated in rfc6996
        msg = f"ASN {asn} is out of range. Must be between 0 and 4294967295"
        raise ASNError(msg)

    return True


def strip_distinguished_prefix(prefix: str) -> IPv4Interface | IPv6Interface:
    """strip_distinguished_prefix Takes a prefix marked with a route distinguisher (RD) and spits out just the prefix.

    An example of this can be shown with the prefixes "293:64666:192.0.2.0/24", or "293:64666:2001:db88::1/128", this
    function would strip down to to `192.0.2.0/24` and `2001:db88::1/128` respectively.

    Args:
        prefix (str): A prefix that has a route distinguisher prefixing the prefix, i.e. "293:64666:192.0.2.0/24", or
            "293:64666:2001:db88::1/128",

    Returns:
        IPv4Interface | IPv6Interface: The formatted IP address object without the RD.
    """
    # Split on only the first two colons and keep only the last value in the resulting list.
    stripped_prefix = prefix.split(":", 2)[-1]
    try:
        return ip_interface(stripped_prefix)
    except ValueError as e:
        logger.exception("Could not properly parse prefix: %s ,received error: %s", prefix, e.message)
