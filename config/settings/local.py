"""Use these settings for local development."""

from django.core.management.utils import get_random_string

from .base import *  # noqa
from .base import AUTH_METHOD, REST_FRAMEWORK, env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = True
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default=get_random_string(chars="abcdefghijklmnopqrstuvwxyz0123456789"),
)
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ["*"]

# CACHES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#caches
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "",
    },
}

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = env("DJANGO_EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")

# WhiteNoise
# ------------------------------------------------------------------------------
# http://whitenoise.evans.io/en/latest/django.html#using-whitenoise-in-development
INSTALLED_APPS = ["whitenoise.runserver_nostatic"] + INSTALLED_APPS  # noqa F405

# django-coverage-plugin
# ------------------------------------------------------------------------------
# https://github.com/nedbat/django_coverage_plugin?tab=readme-ov-file#django-template-coveragepy-plugin
TEMPLATES[0]["OPTIONS"]["debug"] = True  # noqa F405

# django-debug-toolbar
# ------------------------------------------------------------------------------
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#prerequisites
INSTALLED_APPS += ["debug_toolbar"]
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#middleware
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]  # noqa F405
# https://django-debug-toolbar.readthedocs.io/en/latest/configuration.html#debug-toolbar-config
DEBUG_TOOLBAR_CONFIG = {
    "DISABLE_PANELS": ["debug_toolbar.panels.redirects.RedirectsPanel"],
    "SHOW_TEMPLATE_CONTEXT": True,
}
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#internal-ips
INTERNAL_IPS = ["127.0.0.1", "10.0.2.2"]
if env("USE_DOCKER", default="no") == "yes":
    import socket

    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    # This comes from the cookiecutter and while we don't like it, it's not worth the effort to fix yet
    # ruff: noqa: RUF005
    INTERNAL_IPS += [".".join(ip.split(".")[:-1] + ["1"]) for ip in ips]

# django-extensions
# ------------------------------------------------------------------------------
# https://django-extensions.readthedocs.io/en/latest/installation_instructions.html#configuration
INSTALLED_APPS += ["django_extensions"]

# Your stuff...
# ------------------------------------------------------------------------------
REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"] = ("rest_framework.permissions.IsAdminUser",)

# Behave Django testing framework
INSTALLED_APPS += ["behave_django"]

# AUTHENTICATION
# ------------------------------------------------------------------------------
# We shouldn't be using OIDC in local dev mode as of now, but might be worth pursuing later
if AUTH_METHOD == "oidc":
    msg = "oidc is not yet implemented"
    raise NotImplementedError(msg)

# https://docs.djangoproject.com/en/dev/ref/settings/#login-url
LOGIN_URL = "admin:login"
# https://docs.djangoproject.com/en/dev/ref/settings/#logout-url
LOGOUT_URL = "admin:logout"


SCRAM_HOSTNAME = env(
    "SCRAM_HOSTNAME",
    default="scram_hostname_not_set",
)
