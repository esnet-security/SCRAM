"""Define URLs for the WebSocket consumers.

Here, we create regex matching URLs for translator_* and webui_* websocket URLs and route them to the right consumer.
"""

from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(
        r"ws/route_manager/translator_(?P<translator_type>\w+)/$",
        consumers.TranslatorConsumer.as_asgi(),
    ),
    re_path(
        r"ws/route_manager/webui_(?P<actiontype>\w+)/$",
        consumers.WebUIConsumer.as_asgi(),
    ),
]
