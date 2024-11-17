"""
With these settings, tests run faster.
"""

import os

from .base import *  # noqa
from .base import env

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
# Extend middleware to add OIDC middleware
MIDDLEWARE += ["mozilla_django_oidc.middleware.SessionRefresh"]  # noqa F405

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

OIDC_RP_CLIENT_ID = os.environ.get("OIDC_RP_CLIENT_ID", "client_id")
OIDC_RP_CLIENT_SECRET = os.environ.get("OIDC_RP_CLIENT_SECRET", "client_secret")
