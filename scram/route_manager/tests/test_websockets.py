import json
from asyncio import gather
from contextlib import asynccontextmanager

from asgiref.sync import sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from config.routing import websocket_urlpatterns
from scram.route_manager.models import ActionType, Client, WebSocketMessage, WebSocketSequenceElement


@asynccontextmanager
async def get_communicators(actiontypes, should_match, *args, **kwds):
    """Creates a set of communicators, and then handles tear-down.

    Given two lists of the same length, a set of actiontypes, and set of boolean values,
    creates that many communicators, one for each actiontype-bool pair.

    The boolean determines whether or not we're expecting to recieve a message to that communicator.

    Returns a list of (communicator, should_match bool) pairs.
    """
    assert len(actiontypes) == len(should_match)

    router = URLRouter(websocket_urlpatterns)
    communicators = [
        WebsocketCommunicator(router, f"/ws/route_manager/translator_{actiontype}/") for actiontype in actiontypes
    ]
    response = zip(communicators, should_match)

    for communicator, should_match in response:
        connected, subprotocol = await communicator.connect()
        assert connected

    try:
        yield response

    finally:
        for communicator, should_match in response:
            await communicator.disconnect()


class TranslatorBaseCase(TestCase):
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

        wsm, _ = WebSocketMessage.objects.get_or_create(msg_type="translator_add", msg_data_route_field="route")
        _, _ = WebSocketSequenceElement.objects.get_or_create(
            websocketmessage=wsm, verb="A", action_type=self.actiontype
        )

    async def get_messages(self, communicator, messages, should_match):
        """Receive a number of messages from the WebSocket and validate them."""
        for msg in messages:
            response = json.loads(await communicator.receive_from())
            match = response == msg
            assert match == should_match

    async def add_ip(self, ip, mask):
        async with get_communicators(self.actiontypes, self.should_match) as communicators:
            await self.api_create_entry(ip)

            # A list of that many function calls to verify the response
            get_message_func_calls = [
                self.get_messages(c, self.generate_add_msgs(ip, mask), should_match)
                for c, should_match in communicators
            ]

            # Turn our list into parameters to the function and await them all
            await gather(*get_message_func_calls)

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


class TranslatorSimpleTestCase(TranslatorBaseCase):
    """Three translators in the same group, single IP, ensure we get the message we expect."""

    def setUp(self):
        # First call TranslatorBaseCase.setUp()
        super().setUp()

        self.actiontypes = ["block"] * 3
        self.should_match = [True] * 3
        self.generate_add_msgs = [lambda ip, mask: {"type": "translator_add", "message": {"route": f"{ip}/{mask}"}}]

    async def test_add_v4(self):
        await self.add_ip("1.2.3.4", 32)

    async def test_add_v6(self):
        await self.add_ip("2001::", 128)


class TranslatorDontCrossTheStreamsTestCase(TranslatorBaseCase):
    """Two translators in the same group, two in another group, single IP, ensure we get only the messages we expect."""

    def setUp(self):
        # First call TranslatorBaseCase.setUp()
        super().setUp()

        self.actiontypes = ["block", "block", "noop", "noop"]
        self.should_match = [True, True, False, False]
        self.generate_add_msgs = [lambda ip, mask: {"type": "translator_add", "message": {"route": f"{ip}/{mask}"}}]

    async def test_add_v4(self):
        await self.add_ip("1.2.3.4", 32)

    async def test_add_v6(self):
        await self.add_ip("2001::", 128)


class TranslatorSequenceTestCase(TranslatorBaseCase):
    """Test a sequence of WebSocket messages."""

    def setUp(self):
        # First call TranslatorBaseCase.setUp()
        super().setUp()

        wsm2 = WebSocketMessage.objects.create(msg_type="translator_add", msg_data_route_field="foo")
        _ = WebSocketSequenceElement.objects.create(
            websocketmessage=wsm2, verb="A", action_type=self.actiontype, order_num=20
        )
        wsm3 = WebSocketMessage.objects.create(msg_type="translator_add", msg_data_route_field="bar")
        _ = WebSocketSequenceElement.objects.create(
            websocketmessage=wsm3, verb="A", action_type=self.actiontype, order_num=2
        )

        self.actiontypes = ["block"] * 3
        self.should_match = [True] * 3
        self.generate_add_msgs = [
            lambda ip, mask: {"type": "translator_add", "message": {"route": f"{ip}/{mask}"}},  # order_num=0
            lambda ip, mask: {"type": "translator_add", "message": {"bar": f"{ip}/{mask}"}},  # order_num=2
            lambda ip, mask: {"type": "translator_add", "message": {"foo": f"{ip}/{mask}"}},  # order_num=20
        ]

    async def test_add_v4(self):
        await self.add_ip("1.2.3.4", 32)

    async def test_add_v6(self):
        await self.add_ip("2001::", 128)


class TranslatorParametersTestCase(TranslatorBaseCase):
    """Additional parameters in the JSONField."""

    def setUp(self):
        # First call TranslatorBaseCase.setUp()
        super().setUp()

        self.actiontypes = ["block"] * 3
        self.should_match = [True] * 3

        wsm = WebSocketMessage.objects.get(msg_type="translator_add", msg_data_route_field="route")
        wsm.msg_data = {"asn": 65550, "community": 100, "route": "Ensure this gets overwritten."}
        wsm.save()

        self.generate_add_msgs = [
            lambda ip, mask: {
                "type": "translator_add",
                "message": {"asn": 65550, "community": 100, "route": f"{ip}/{mask}"},
            }
        ]

    async def test_add_v4(self):
        await self.add_ip("1.2.3.4", 32)

    async def test_add_v6(self):
        await self.add_ip("2001::", 128)
