import json
from channels.generic.websocket import AsyncWebsocketConsumer


class RouteConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.actiontype = self.scope["url_route"]["kwargs"]["actiontype"]
        self.group_name = f"xlator_{self.actiontype}"

        # Join group
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        print(f"Got message: {message!r}.")

    # Broadcast a new block
    async def add_block(self, event):
        await self.send(text_data=json.dumps(event))

    # Broadcast the removal of a block
    async def remove_block(self, event):
        await self.send(text_data=json.dumps(event))
