"""A Module for defining shared code."""

import secrets
import string


def make_random_password(length: int = 20, min_digits: int = 5, max_attempts: int = 10000) -> str:
    """make_random_password replaces the deprecated django make_random_password function.

    Generates a random password of a specified length containing at least a specified number of digits using the
    official python best practices and some additional sanity checks. The python docs for this can be found at
    https://docs.python.org/3/library/secrets.html#recipes-and-best-practices. Note that generating long passwords
    with a high number of digits (>100) is inefficient and should be avoided. This password should only be used for
    temporary purposes, such as for a user to log in to the web interface and change their password.

    Args:
        length (int, optional): The total length of the password to generate. Defaults to 20.
        min_digits (int, optional): The minimum number of digits the password needs. Defaults to 5.
        max_attempts (int, optional): The maximum number of attempts to generate a valid password. Defaults to 10000.

    Raises:
        ValueError: Password length must be at least 1
        ValueError: min_digits cannot be negative
        ValueError: min_digits cannot exceed password length
        ValueError: For performance reasons, min_digits cannot exceed 30% of the password length
        RuntimeError: Failed to generate a valid password after max_attempts attempts

    Returns:
        password (str): The generated password.
    """
    if length < 1:
        message = "Password length must be at least 1"
        raise ValueError(message)
    if min_digits < 0:
        message = "min_digits cannot be negative"
        raise ValueError(message)
    if min_digits > length:
        message = "min_digits cannot exceed password length"
        raise ValueError(message)
    # Only allow a somewhat arbitrary threshold of 30% of the password length for min_digits, for performance reasons.
    if min_digits > length * 0.3:
        message = "For performance reasons, min_digits cannot exceed 30% of the password length"
        raise ValueError(message)

    alphabet = string.ascii_letters + string.digits

    for _attempt in range(max_attempts):
        password = "".join(secrets.choice(alphabet) for _i in range(length))
        if (
            any(c.islower() for c in password)
            and any(c.isupper() for c in password)
            and sum(c.isdigit() for c in password) >= min_digits
        ):
            return password

    # If we reached this point, we failed to generate a valid password after max_attempts attempts, likely due to the
    # required password length being very long and the min_digits being high.
    message = f"Failed to generate a valid password after {max_attempts} attempts"
    raise RuntimeError(message)


def get_client_ip(request) -> str | None:
    """Get the client's IP address from the request.

    Checks the HTTP_X_FORWARDED_FOR header first, then falls back to REMOTE_ADDR.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip
