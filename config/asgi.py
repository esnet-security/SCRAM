"""ASGI config for SCRAM project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/dev/howto/deployment/asgi/

"""

import logging
import os
import sys
from pathlib import Path

# TODO: from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

# TODO: from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

# Here we setup a debugger if this is desired. This obviously should not be run in production.
debug = os.environ.get("DEBUG")
if debug:
    logging.info("Django is set to use a debugger. Provided debug mode: %s", debug)
    if debug == "pycharm-pydevd":
        logging.info("Entering debug mode for pycharm, make sure the debug server is running in PyCharm!")

        import pydevd_pycharm

        pydevd_pycharm.settrace("host.docker.internal", port=56783, stdoutToServer=True, stderrToServer=True)

        logging.info("Debugger started.")
    elif debug == "debugpy":
        logging.info("Entering debug mode for debugpy (VSCode)")

        import debugpy

        debugpy.listen(("0.0.0.0", 56780))  # noqa S104 (doesn't like binding to all interfaces)

        logging.info("Debugger listening on port 56780.")
    else:
        logging.warning("Invalid debug mode given: %s. Debugger not started", debug)

# This allows easy placement of apps within the interior
# scram directory.
ROOT_DIR = Path(__file__).resolve(strict=True).parent.parent
sys.path.append(str(ROOT_DIR / "scram"))

# If DJANGO_SETTINGS_MODULE is unset, default to the local settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

# This application object is used by any ASGI server configured to use this file.
django_application = get_asgi_application()

from . import routing as scram_routing  # noqa: E402

ws_application = URLRouter(scram_routing.websocket_urlpatterns)

# Events are published to a specific channel via api/views.py.
# Publishing to an event that's not routed will result in events that go nowhere.
application = ProtocolTypeRouter(
    {
        "http": django_application,
        "websocket": ws_application,
    },
)
