from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(
        r"ws/route_manager/(?P<actiontype>\w+)/$", consumers.RouteConsumer.as_asgi()
    ),
]
