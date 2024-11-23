"""Define URLs for the WebSocket consumers."""

from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/route_manager/translator_(?P<actiontype>\w+)/$", consumers.TranslatorConsumer.as_asgi()),
    re_path(r"ws/route_manager/webui_(?P<actiontype>\w+)/$", consumers.WebUIConsumer.as_asgi()),
]
