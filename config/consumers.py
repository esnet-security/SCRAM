"""Define logic for the WebSocket consumers."""

import logging
import time

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.core.cache import cache

from scram.route_manager.models import Entry, WebSocketSequenceElement

logger = logging.getLogger(__name__)


class TranslatorConsumer(AsyncJsonWebsocketConsumer):
    """Handle messages from the Translator(s)."""

    async def connect(self):
        """Handle the initial connection with adding to the right group."""
        logger.info("Translator connected")
        self.actiontype = self.scope["url_route"]["kwargs"]["actiontype"]
        self.translator_group = f"translator_{self.actiontype}"

        await self.channel_layer.group_add(self.translator_group, self.channel_name)
        await self.accept()

        # Update connected translator count in cache
        def update_connect_cache():
            cache.get_or_set(f"translator_count:{self.actiontype}", 0)
            cache.incr(f"translator_count:{self.actiontype}")

        await sync_to_async(update_connect_cache)()

        # Filter WebSocketSequenceElements by actiontype
        elements = await sync_to_async(list)(
            WebSocketSequenceElement.objects.filter(action_type__name=self.actiontype).order_by("order_num"),
        )
        if not elements:
            logger.warning("No elements found for actiontype=%s.", self.actiontype)
            return

        # Avoid lazy evaluation
        routes = await sync_to_async(list)(Entry.objects.filter(is_active=True).values_list("route__route", flat=True))

        for route in routes:
            for element in elements:
                msg = await sync_to_async(lambda e: e.websocketmessage)(element)
                msg.msg_data[msg.msg_data_route_field] = str(route)
                await self.send_json({"type": msg.msg_type, "message": msg.msg_data})

    async def disconnect(self, close_code):
        """Discard any remaining messages on disconnect."""
        logger.info("Disconnect received: %s", close_code)
        await self.channel_layer.group_discard(self.translator_group, self.channel_name)

        # Update connected translator count in cache
        def update_disconnect_cache():
            try:
                if cache.get(f"translator_count:{self.actiontype}", 0) > 0:
                    cache.decr(f"translator_count:{self.actiontype}")
            except (ValueError, TypeError):
                cache.set(f"translator_count:{self.actiontype}", 0)

        await sync_to_async(update_disconnect_cache)()

    async def receive_json(self, content):
        """Handle a WebSocket message."""
        if content["type"] == "translator_heartbeat":
            # We received a heartbeat from a translator, update stats in cache.
            msg = content["message"]
            stats = {
                "v4_count": msg["v4_count"],
                "v6_count": msg["v6_count"],
                "last_seen": time.time(),
            }
            cache_key = f"translator_stats:{self.actiontype}"
            logger.info("Received heartbeat for %s: %s (Key: %s)", self.actiontype, stats, cache_key)
            await sync_to_async(cache.set)(cache_key, stats, timeout=300)
        elif content["type"] == "translator_check_resp":
            # We received a check response from a translator, forward to web UI.
            channel = content.pop("channel")
            content["type"] = "wui_check_resp"
            await self.channel_layer.send(channel, content)

    async def _send_event(self, event):
        await self.send_json(event)

    # Tell all translators of this actiontype of an addition of a route.
    translator_add = _send_event
    # Tell all translators of this actiontype of a withdrawal of a route.
    translator_remove = _send_event
    # Tell all translators of this actiontype to withdraw ALL routes.
    translator_remove_all = _send_event
    # Send a query to all translators if a route is announced.
    translator_check = _send_event


class WebUIConsumer(AsyncJsonWebsocketConsumer):
    """Handle messages from the Web UI."""

    async def connect(self):
        """Handle the initial connection with adding to the right group."""
        self.actiontype = self.scope["url_route"]["kwargs"]["actiontype"]
        self.translator_group = f"translator_{self.actiontype}"

        await self.accept()

    async def receive_json(self, content):
        """Receive message from WebSocket."""
        if content["type"] == "wui_check_req":
            # Web UI asks us to check; forward to translator(s)
            await self.channel_layer.group_send(
                self.translator_group,
                {
                    "type": "translator_check",
                    "channel": self.channel_name,
                    "message": content["message"],
                },
            )

    async def wui_check_resp(self, event):
        """Forward a message to the correct Websocket."""
        await self.send_json(event)
