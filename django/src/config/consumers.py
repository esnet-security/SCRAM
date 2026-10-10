"""Define logic for the WebSocket consumers."""

import logging
import time

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.core.cache import cache

from scram.route_manager.models import ActionType, Entry, TranslatorType

logger = logging.getLogger(__name__)

# Defines our custom close code so translators can be informed about config errrors.
UNKNOWN_TRANSLATOR_TYPE = 4404

# Heartbeats refresh this, so counts from translators that died without disconnecting age out.
TRANSLATOR_COUNT_TIMEOUT = 120


class TranslatorConsumer(AsyncJsonWebsocketConsumer):
    """Handle messages from the Translator(s)."""

    async def connect(self) -> None:
        """Handle the initial connection with adding to the right group.

        When a translator connects, it will receive all active entries that the translator is responsible for. If a
        translator connects to a group for a translator type that doesn't exist, it receives a 4404 close code.
        """

        name = self.scope["url_route"]["kwargs"]["translator_type"]
        self.translator_type = await database_sync_to_async(
            TranslatorType.objects.filter(name=name).first
        )()

        # Handle the case of a translator connecting to a non-existent translator type.
        if self.translator_type is None:
            logger.error("Rejecting translator: unknown translator type %r", name)

            await (
                self.accept()
            )  # it's weird, but we accept first so we can send a close message.
            await self.close(
                code=UNKNOWN_TRANSLATOR_TYPE,
                reason=f"Unknown translator type {name!r}, doulbe check the SCRAM URL.",
            )
            return

        logger.info("Translator connected: %s", name)
        await self.channel_layer.group_add(
            self.translator_type.group, self.channel_name
        )
        await self.accept()

        # Update connected translator count in cache
        def update_connect_cache() -> None:
            cache.get_or_set(
                f"translator_count:{name}", 0, timeout=TRANSLATOR_COUNT_TIMEOUT
            )
            cache.incr(f"translator_count:{name}")

        await database_sync_to_async(update_connect_cache)()

        entries = await database_sync_to_async(list)(
            Entry.objects.filter(
                is_active=True, actiontype__translator_types=self.translator_type
            ).select_related("actiontype", "route")
        )
        for entry in entries:
            await self.send_json(entry.actiontype.message("add", entry.target))

    async def disconnect(self, close_code) -> None:
        """Discard any remaining messages on disconnect."""
        logger.info("Disconnect received: %s", close_code)
        if self.translator_type is None:
            return
        await self.channel_layer.group_discard(
            self.translator_type.group, self.channel_name
        )

        # Update connected translator count in cache
        def update_disconnect_cache() -> None:
            cache_key = f"translator_count:{self.translator_type.name}"
            try:
                if cache.get(cache_key, 0) > 0:
                    cache.decr(cache_key)
            except (ValueError, TypeError):
                cache.set(cache_key, 0)

        await database_sync_to_async(update_disconnect_cache)()

    async def receive_json(self, content) -> None:
        """Handle a WebSocket message."""
        if content["type"] == "translator_heartbeat":
            # We received a heartbeat from a translator, update stats in cache.
            # Route counts are optional for nowsince not every translator backend can report them uniquely (flowspec
            # for the time being). This also means that route counts for GoBGP are just combined since it's from the
            # RIB. We should consider fixing that in the translator which should be pretty easy when writing the
            # handler for `translator_blah_check` messages to filter by AF or some other criteria.
            msg = content.get("message", {})
            stats = {
                "v4_count": msg.get("v4_count", 0),
                "v6_count": msg.get("v6_count", 0),
                "last_seen": time.time(),
            }
            cache_key = f"translator_stats:{self.translator_type.name}"
            logger.debug(
                "Received heartbeat for %s: %s (Key: %s)",
                self.translator_type,
                stats,
                cache_key,
            )
            await database_sync_to_async(cache.set)(cache_key, stats, timeout=300)
            await database_sync_to_async(cache.touch)(
                f"translator_count:{self.translator_type.name}",
                TRANSLATOR_COUNT_TIMEOUT,
            )
        elif content["type"] == "translator_check_resp":
            # We received a check response from a translator, forward to web UI.
            channel = content.pop("channel")
            content["type"] = "wui_check_resp"
            await self.channel_layer.send(channel, content)

    async def dispatch(self, message) -> None:
        """Forwards any translator_* events to send_json().

        Previously, we had explicit handlers for each translator_* event type that all called .send_json(), but now we
        just forward them all to send_json() dynamically to avoid having to update django code whenever a new event
        type is added.
        """
        if message["type"].startswith("translator_"):
            await self.send_json(message)
        else:
            await super().dispatch(message)

class WebUIConsumer(AsyncJsonWebsocketConsumer):
    """Handle messages from the Web UI."""

    async def connect(self) -> None:
        """Handle the initial connection with adding to the right group.

        Basically, here we look up the action type for the checks that the Web UI is interested in and make sure
        that those checks go to the correct translator group(s).
        """
        name = self.scope["url_route"]["kwargs"]["actiontype"]

        def load() -> tuple[ActionType, list[str]]:
            actiontype = ActionType.objects.get(name=name)
            return actiontype, [tt.group for tt in actiontype.translator_types.all()]

        self.actiontype, self.check_groups = await database_sync_to_async(load)()
        await self.accept()

    async def receive_json(self, content) -> None:
        """Receive message from WebSocket.

        If you have multiple translators for the same action type, the UI will only really ever show the first one to
        respond to the check request.
        """
        if content["type"] == "wui_check_req":
            # Web UI asks us to check; forward to translator(s)
            event = self.actiontype.message("check", content["message"]["route"])
            event["message"].update(content["message"])
            event["channel"] = self.channel_name
            for group in self.check_groups:
                await self.channel_layer.group_send(group, event)

    async def wui_check_resp(self, event):
        """Forward a message to the correct Websocket."""
        await self.send_json(event)
