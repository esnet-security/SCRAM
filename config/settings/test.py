"""With these settings, tests run faster."""

from django.core.management.utils import get_random_secret_key

from .base import *  # noqa
from .base import env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default=get_random_secret_key(),
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
    ),
]
TEMPLATES[0]["OPTIONS"]["debug"] = True  # noqa F405

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Your stuff...
# ------------------------------------------------------------------------------
# These variables are required by the ESnetAuthBackend called in our OidcTest case
OIDC_OP_JWKS_ENDPOINT = "https://example.com/auth/realms/example/protocol/openid-connect/certs"
OIDC_OP_AUTHORIZATION_ENDPOINT = "https://example.com/auth/realms/example/protocol/openid-connect/auth"
OIDC_OP_TOKEN_ENDPOINT = "https://example.com/auth/realms/example/protocol/openid-connect/token"
OIDC_OP_USER_ENDPOINT = "https://example.com/auth/realms/example/protocol/openid-connect/userinfo"
OIDC_RP_SIGN_ALGO = "RS256"
OIDC_RP_CLIENT_ID = ""
OIDC_RP_CLIENT_SECRET = ""

SCRAM_HOSTNAME = env(
    "SCRAM_HOSTNAME",
    default="scram_hostname_not_set",  # TODO: Change this? Think about the implications here.
)
