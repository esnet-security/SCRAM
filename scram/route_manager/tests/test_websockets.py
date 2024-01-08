from asgiref.sync import sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
import json

from config.consumers import TranslatorConsumer
from config.routing import websocket_urlpatterns
from scram.route_manager.models import ActionType, Client, Entry, Route, WebSocketMessage, WebSocketSequenceElement

from _pytest.assertion import truncate
truncate.DEFAULT_MAX_LINES = 9999
truncate.DEFAULT_MAX_CHARS = 9999

class TestTranslator(TestCase):
    def setUp(self):
        # TODO: This is copied from test_api; should de-dupe this.
        self.url = reverse("api:v1:entry-list")
        self.superuser = get_user_model().objects.create_superuser("admin", "admin@example.net", "admintestpassword")
        self.client.login(username="admin", password="admintestpassword")
        self.uuid = "0e7e1cbd-7d73-4968-bc4b-ce3265dc2fd3"

        self.action_name = "block"

        self.actiontype, created = ActionType.objects.get_or_create(name=self.action_name)
        self.actiontype.save()

        self.authorized_client = Client.objects.create(
            hostname="authorized_client.example.net",
            uuid=self.uuid,
            is_authorized=True,
        )
        self.authorized_client.authorized_actiontypes.set([self.actiontype])

        wsm = WebSocketMessage.objects.create(msg_type="translator_add", msg_data_route_field="route")
        wsse = WebSocketSequenceElement.objects.create(websocketmessage=wsm, verb="A", action_type=self.actiontype)


    async def create_communicator(self, name):
        # Each one needs its own, so we can't do this in setUp
        router = URLRouter(websocket_urlpatterns)
        communicator = WebsocketCommunicator(router, f"/ws/route_manager/{name}/")

        connected, subprotocol = await communicator.connect()
        assert connected

        return communicator

    async def add_ip(self, ip, mask):
        communicator = await self.create_communicator(f"translator_{self.action_name}")

        await self.api_create_entry(ip)
        response = json.loads(await communicator.receive_from())
        # Keep in sync with translator API
        assert response == {"type": "translator_add", "message": {"route": f"{ip}/{mask}"}}

        await communicator.disconnect()

    async def test_add_v4(self):
        await self.add_ip("1.2.3.4", 32)

    async def test_add_v6(self):
        await self.add_ip("2001::", 128)

    # Django ensures that the create is synchronous, so we have some extra steps to do
    @sync_to_async
    def api_create_entry(self, route):
        return self.client.post(
            self.url,
            {
                "route": route,
                "comment": "test",
                "uuid": self.uuid,
            },
            format="json",
        )
