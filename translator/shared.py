"""Provide a location for code that we want to share between all translators."""

from exceptions import ASNError

MAX_ASN_VAL = 2**32 - 1


def asn_is_valid(asn: int) -> bool:
    """asn_is_valid makes sure that an ASN passed in is a valid 2 or 4 Byte ASN.

    Args:
        asn (int): The Autonomous System Number that we want to validate

    Raises:
        ASNError: If the ASN is not between 0 and 4294967295 or is not an integer.

    Returns:
        bool: _description_

    """
    if not isinstance(asn, int):
        msg = f"ASN {asn} is not an Integer, has type {type(asn)}"
        raise ASNError(msg)
    if not 0 < asn < MAX_ASN_VAL:
        # This is the max as stated in rfc6996
        msg = f"ASN {asn} is out of range. Must be between 0 and 4294967295"
        raise ASNError(msg)

    return True
