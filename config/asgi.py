"""
ASGI config for SCRAM project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/dev/howto/deployment/asgi/

"""
import os
import sys
from pathlib import Path

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.conf.urls import url
from channels.auth import AuthMiddlewareStack
import django_eventstream


# This allows easy placement of apps within the interior
# scram directory.
ROOT_DIR = Path(__file__).resolve(strict=True).parent.parent
sys.path.append(str(ROOT_DIR / "scram"))

# If DJANGO_SETTINGS_MODULE is unset, default to the local settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

# This application object is used by any ASGI server configured to use this file.
django_application = get_asgi_application()
# Apply ASGI middleware here.
# from helloworld.asgi import HelloWorldApplication
# application = HelloWorldApplication(application)

# Events are published to a specific channel via api/views.py.
# Publishing to an event that's not routed will result in events that go nowhere.
application = ProtocolTypeRouter({
    'http': URLRouter([
        # Must match the URL used by add_path
        url(r'^events/blocks/', AuthMiddlewareStack(
            URLRouter(django_eventstream.routing.urlpatterns)
            # Must match a channel name in api/views.py
        ), { 'channels': ['block'] }),
        url(r'', django_application),
    ]),
})

# # Import websocket application here, so apps from django_application are loaded first
# from config.websocket import websocket_application  # noqa isort:skip


# async def application(scope, receive, send):
#     if scope["type"] == "http":
#         await django_application(scope, receive, send)
#     elif scope["type"] == "websocket":
#         await websocket_application(scope, receive, send)
#     else:
#         raise NotImplementedError(f"Unknown scope type {scope['type']}")
