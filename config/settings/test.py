"""
With these settings, tests run faster.
"""

import os

from .base import *  # noqa
from .base import AUTH_METHOD, env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="qotrPVH3oE4bohX1nhiG7wlWu9BW3ZHEMGWP4ejTx4nWsKpRmECBQtiSVMFyFLLv",
)
# https://docs.djangoproject.com/en/dev/ref/settings/#test-runner
TEST_RUNNER = "django.test.runner.DiscoverRunner"

# PASSWORDS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# TEMPLATES
# ------------------------------------------------------------------------------
TEMPLATES[-1]["OPTIONS"]["loaders"] = [  # type: ignore[index] # noqa F405
    (
        "django.template.loaders.cached.Loader",
        [
            "django.template.loaders.filesystem.Loader",
            "django.template.loaders.app_directories.Loader",
        ],
    )
]

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Your stuff...
# ------------------------------------------------------------------------------
if AUTH_METHOD == "oidc":
    # Extend middleware to add OIDC middleware
    MIDDLEWARE += ["mozilla_django_oidc.middleware.SessionRefresh"]  # noqa F405

    # Extend middleware to add OIDC auth backend
    AUTHENTICATION_BACKENDS += ["scram.route_manager.authentication_backends.ESnetAuthBackend"]  # noqa F405

    # https://docs.djangoproject.com/en/dev/ref/settings/#login-url
    LOGIN_URL = "oidc_authentication_init"

    # https://docs.djangoproject.com/en/dev/ref/settings/#login-redirect-url
    LOGIN_REDIRECT_URL = "route_manager:home"

    # https://docs.djangoproject.com/en/dev/ref/settings/#logout-url
    LOGOUT_URL = "oidc_logout"

    # Need to point somewhere otherwise /oidc/logout/ redirects to /oidc/logout/None which 404s
    # https://github.com/mozilla/mozilla-django-oidc/issues/118
    # Using `/` because named urls don't work for this package
    # https://github.com/mozilla/mozilla-django-oidc/issues/434
    LOGOUT_REDIRECT_URL = "route_manager:home"

    OIDC_OP_JWKS_ENDPOINT = os.environ.get(
        "OIDC_OP_JWKS_ENDPOINT",
        "https://example.com/auth/realms/example/protocol/openid-connect/certs",
    )
    OIDC_OP_AUTHORIZATION_ENDPOINT = os.environ.get(
        "OIDC_OP_AUTHORIZATION_ENDPOINT",
        "https://example.com/auth/realms/example/protocol/openid-connect/auth",
    )
    OIDC_OP_TOKEN_ENDPOINT = os.environ.get(
        "OIDC_OP_TOKEN_ENDPOINT",
        "https://example.com/auth/realms/example/protocol/openid-connect/token",
    )
    OIDC_OP_USER_ENDPOINT = os.environ.get(
        "OIDC_OP_USER_ENDPOINT",
        "https://example.com/auth/realms/example/protocol/openid-connect/userinfo",
    )
    OIDC_RP_SIGN_ALGO = "RS256"

    OIDC_RP_CLIENT_ID = os.environ.get("OIDC_RP_CLIENT_ID")
    OIDC_RP_CLIENT_SECRET = os.environ.get("OIDC_RP_CLIENT_SECRET")

elif AUTH_METHOD == "local":
    # https://docs.djangoproject.com/en/dev/ref/settings/#login-url
    LOGIN_URL = "local_auth:login"

    # https://docs.djangoproject.com/en/dev/ref/settings/#login-redirect-url
    LOGIN_REDIRECT_URL = "route_manager:home"

    # https://docs.djangoproject.com/en/dev/ref/settings/#logout-url
    LOGOUT_URL = "local_auth:logout"

    # https://docs.djangoproject.com/en/dev/ref/settings/#logout-redirect-url
    LOGOUT_REDIRECT_URL = "route_manager:home"
else:
    raise Exception(f"Invalid authentication method: {AUTH_METHOD}. Please choose 'local' or 'oidc'")
