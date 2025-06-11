"""A Module for defining shared code."""

import secrets
import string


def make_random_password(length: int = 10, min_digits: int = 3) -> str:
    """make_random_password django deprecated this function so let's roll our own, wcgw.

    Args:
        length (int, optional): The password length. Defaults to 10.
        min_digits (int, optional): The minimum number of digits. Defaults to 3.

    Returns:
        str: The generated password.
    """
    # todo: add sanity checks for length and min_digits, i.e. min_digits <= length, and do something about long
    # passwords which will prolly take forever.
    alphabet = string.ascii_letters + string.digits
    while True:
        password = "".join(secrets.choice(alphabet) for i in range(length))
        if (
            any(c.islower() for c in password)
            and any(c.isupper() for c in password)
            and sum(c.isdigit() for c in password) >= min_digits
        ):
            return password
