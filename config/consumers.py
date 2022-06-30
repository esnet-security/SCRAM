from channels.generic.websocket import AsyncJsonWebsocketConsumer


class TranslatorConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.actiontype = self.scope["url_route"]["kwargs"]["actiontype"]
        self.xlator_group = f"xlator_{self.actiontype}"

        await self.channel_layer.group_add(self.xlator_group, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.xlator_group, self.channel_name)

    async def receive_json(self, content):
        """Received a WebSocket message"""
        print("xlator received", content)
        if content['type'] == 'check_block_resp':
            channel = content.pop('channel')
            await self.channel_layer.send(channel, content)

    async def add_block(self, event):
        """Tell all translators of this actiontype of an addition of a route."""
        await self.send_json(event)

    async def remove_block(self, event):
        """Tell all translators of this actiontype of a withdrawal of a route."""
        await self.send_json(event)

    async def check_block(self, event):
        """Send a query to all translators if a route is announced."""
        await self.send_json(event)


class WebUIConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.actiontype = self.scope["url_route"]["kwargs"]["actiontype"]
        self.xlator_group = f"xlator_{self.actiontype}"

        await self.accept()

    # Receive message from WebSocket
    async def receive_json(self, content):
        if content['type'] == 'check_block_req':
            print("**", content)
            await self.channel_layer.group_send(
                self.xlator_group,
                {"type": "check_block",
                 "channel": self.channel_name,
                 "message": content['message'],
                 },
            )

    async def check_block_resp(self, event):
        """Forward a message to the correct Websocket."""
        await self.send_json(event)
