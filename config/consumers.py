import logging

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from scram.route_manager.models import Entry, WebSocketSequenceElement


class TranslatorConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        logging.info("Translator connected")
        self.actiontype = self.scope["url_route"]["kwargs"]["actiontype"]
        self.translator_group = f"translator_{self.actiontype}"

        await self.channel_layer.group_add(self.translator_group, self.channel_name)
        await self.accept()

        # Filter WebSocketSequenceElements by actiontype
        elements = await sync_to_async(list)(
            WebSocketSequenceElement.objects.filter(action_type__name=self.actiontype).order_by("order_num")
        )
        if not elements:
            logging.warning(f"No elements found for actiontype={self.actiontype}.")
            return

        # Avoid lazy evaluation
        routes = await sync_to_async(list)(Entry.objects.filter(is_active=True).values_list("route__route", flat=True))

        for route in routes:
            for element in elements:
                msg = await sync_to_async(lambda: element.websocketmessage)()
                msg.msg_data[msg.msg_data_route_field] = str(route)
                await self.send_json({"type": msg.msg_type, "message": msg.msg_data})

    async def disconnect(self, close_code):
        logging.info(f"Disconnect received: {close_code}")
        await self.channel_layer.group_discard(self.translator_group, self.channel_name)

    async def receive_json(self, content):
        """Received a WebSocket message"""
        if content["type"] == "translator_check_resp":
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
    async def connect(self):
        self.actiontype = self.scope["url_route"]["kwargs"]["actiontype"]
        self.translator_group = f"translator_{self.actiontype}"

        await self.accept()

    # Receive message from WebSocket
    async def receive_json(self, content):
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
