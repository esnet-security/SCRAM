"""Define unit tests for the websockets-based communication."""

import json
from asyncio import gather, wait_for
from contextlib import asynccontextmanager

from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from django.urls import reverse
from rest_framework import status

from config.consumers import UNKNOWN_TRANSLATOR_TYPE
from config.routing import websocket_urlpatterns
from scram.route_manager.models import (
    ActionType,
    Client,
    Entry,
    Route,
    TranslatorType,
)

router = URLRouter(websocket_urlpatterns)


async def wait_for_connect(communicator):
    """Consumers handle messages in order, so getting this reply back proves connect() finished its replay."""
    layer = get_channel_layer()
    channel = await layer.new_channel()
    await communicator.send_json_to(
        {"type": "translator_check_resp", "channel": channel, "message": {}}
    )
    await wait_for(layer.receive(channel), timeout=1)


def add_msg(route, **payload):
    """The add message translators should receive for a block entry."""
    return {"type": "translator_block_add", "message": {**payload, "route": route}}


def remove_msg(route):
    """The remove message translators should receive for a block entry."""
    return {"type": "translator_block_remove", "message": {"route": route}}


@asynccontextmanager
async def get_communicators(translator_types, should_match, *args, **kwds):
    """Create a set of communicators, and then handle tear-down.

    Given two lists of the same length, a set of translator types, and set of boolean values,
    creates that many communicators, one for each translator type-bool pair.

    The boolean determines whether or not we're expecting to recieve a message to that communicator.

    Returns a list of (communicator, should_match bool) pairs.
    """
    communicators = [
        WebsocketCommunicator(
            router, f"/ws/route_manager/translator_{translator_type}/"
        )
        for translator_type in translator_types
    ]
    response = list(zip(communicators, should_match, strict=True))

    for communicator, _ in response:
        connected, _ = await communicator.connect()
        assert connected
        await wait_for_connect(communicator)
        # Drop entries replayed on connect so tests only see the messages they are actually causing.
        while not await communicator.receive_nothing(timeout=0):
            await communicator.receive_from()

    try:
        yield response

    finally:
        for communicator, _ in response:
            await communicator.disconnect()


class TestTranslatorBaseCase(TransactionTestCase):
    """Base case that other test cases build on top of. Three translators in one group, test one v4 and one v6."""

    def setUp(self):
        """Set up our test environment."""
        # TODO: This is copied from test_api; should de-dupe this.
        self.url = reverse("api:v1:entry-list")
        self.superuser = get_user_model().objects.create_superuser(
            "admin", "admin@example.net", "admintestpassword"
        )
        self.client.force_login(self.superuser)
        self.uuid = "0e7e1cbd-7d73-4968-bc4b-ce3265dc2fd3"

        self.action_name = "block"

        self.actiontype, _ = ActionType.objects.get_or_create(name=self.action_name)
        self.actiontype.save()

        self.authorized_client = Client.objects.create(
            client_name="authorized_client.example.net",
            uuid=self.uuid,
            is_authorized=True,
        )
        self.authorized_client.authorized_actiontypes.set([self.actiontype])

        self.gobgp, _ = TranslatorType.objects.get_or_create(name="gobgp")
        self.actiontype.translator_types.add(self.gobgp)

        # Set some defaults; some child classes override this
        self.translator_types = ["gobgp"] * 3
        self.should_match = [True] * 3
        self.generate_add_msgs = [
            lambda ip, mask: {
                "type": "translator_block_add",
                "message": {"route": f"{ip}/{mask}"},
            }
        ]

        # Now we run any local setup actions by the child classes
        self.local_setup()

    def local_setup(self):
        """Allow child classes to override this if desired."""
        return

    async def get_messages(self, communicator, messages, should_match):
        """Receive a number of messages from the WebSocket and validate them."""
        if not should_match:
            assert await communicator.receive_nothing()
            return
        for msg in messages:
            response = json.loads(await communicator.receive_from())
            match = response == msg
            assert match == should_match

    async def get_nothings(self, communicator):
        """Check there are no more messages waiting."""
        assert await communicator.receive_nothing(timeout=0.1, interval=0.01) is True

    async def add_ip(self, ip, mask):
        """Ensure we can add an IP to block."""
        async with get_communicators(
            self.translator_types, self.should_match
        ) as communicators:
            await self.api_create_entry(ip)

            # A list of that many function calls to verify the response
            get_message_func_calls = [
                self.get_messages(
                    c, [gen(ip, mask) for gen in self.generate_add_msgs], should_match
                )
                for c, should_match in communicators
            ]

            # Turn our list into parameters to the function and await them all
            await gather(*get_message_func_calls)

            await self.ensure_no_more_msgs(communicators)

    async def ensure_no_more_msgs(self, communicators):
        """Run through all communicators and ensure they have no messages waiting."""
        get_nothing_func_calls = [self.get_nothings(c) for c, _ in communicators]

        # Ensure we don't receive any other messages
        await gather(*get_nothing_func_calls)

    # Django ensures that the create is synchronous, so we have some extra steps to do
    @sync_to_async
    def api_create_entry(self, route):
        """Ensure we can create an Entry via the API."""
        return self.client.post(
            self.url,
            {
                "route": route,
                "comment": "test",
                "uuid": self.uuid,
                "who": "Test User",
            },
            format="json",
        )

    async def test_add_v4(self):
        """Test adding a few v4 routes."""
        await self.add_ip("192.0.2.224", 32)
        await self.add_ip("192.0.2.225", 32)
        await self.add_ip("192.0.2.226", 32)
        await self.add_ip("198.51.100.224", 32)

    async def test_add_v6(self):
        """Test adding a few v6 routes."""
        await self.add_ip("2001:db8:fdf0::", 128)
        await self.add_ip("2001:db8:fdf0::d", 128)
        await self.add_ip("2001:db8:fdf0::db", 128)
        await self.add_ip("2001:db8:fdf0::db8", 128)


class TranslatorDontCrossTheStreamsTestCase(TestTranslatorBaseCase):
    """Two translators in one group, two in another group, single IP, ensure we get only the messages we expect."""

    def local_setup(self):
        """Define the translators and what we expect; frr isn't linked to block."""
        TranslatorType.objects.get_or_create(name="frr")
        self.translator_types = ["gobgp", "gobgp", "frr", "frr"]
        self.should_match = [True, True, False, False]


class TranslatorParametersTestCase(TestTranslatorBaseCase):
    """Additional parameters in the JSONField."""

    def local_setup(self):
        """Define the message we want to send."""
        self.actiontype.payload = {
            "asn": 65550,
            "community": 100,
            "route": "Ensure this gets overwritten.",
        }
        self.actiontype.save()

        self.generate_add_msgs = [
            lambda ip, mask: {
                "type": "translator_block_add",
                "message": {"asn": 65550, "community": 100, "route": f"{ip}/{mask}"},
            },
        ]

    async def test_remove_carries_payload(self):
        """Removes carry the payload too, so translators withdraw the same path they announced."""
        async with get_communicators(["gobgp"], [True]) as [(gobgp, _)]:
            await self.api_create_entry("192.0.2.8/32")
            await gobgp.receive_json_from()
            await sync_to_async(
                lambda: Entry.objects.get(route__route="192.0.2.8/32").delete()
            )()
            assert await gobgp.receive_json_from() == {
                "type": "translator_block_remove",
                "message": {"asn": 65550, "community": 100, "route": "192.0.2.8/32"},
            }


class TranslatorTypeTestCase(TestTranslatorBaseCase):
    """Messages reach exactly the translator types an actiontype is linked to."""

    def local_setup(self):
        """Add frr, which block isn't linked to yet."""
        self.frr, _ = TranslatorType.objects.get_or_create(name="frr")

    @sync_to_async
    def link_in_admin(self, *translator_types):
        """Link action to translator types via admin to trigger messages."""
        response = self.client.post(
            reverse("admin:route_manager_actiontype_change", args=[self.actiontype.pk]),
            {
                "available": "on",
                "payload": "{}",
                "translator_types": [tt.pk for tt in translator_types],
            },
        )
        assert response.status_code == status.HTTP_302_FOUND, response.content

    async def test_check_reaches_every_linked_translator_type(self):
        """Ensure a WUI check goes to every translator type linked to block and each answer comes back."""
        await sync_to_async(self.actiontype.translator_types.add)(self.frr)
        webui = WebsocketCommunicator(router, "/ws/route_manager/webui_block/")
        connected, _ = await webui.connect()
        assert connected
        try:
            async with get_communicators(["gobgp", "frr"], [True, True]) as [
                (gobgp, _),
                (frr, _),
            ]:
                await webui.send_json_to(
                    {
                        "type": "wui_check_req",
                        "message": {"route": "192.0.2.1/32", "row": 1},
                    }
                )
                for translator in (gobgp, frr):
                    check = await translator.receive_json_from()
                    assert check["type"] == "translator_block_check"
                    assert check["message"] == {"route": "192.0.2.1/32", "row": 1}
                    check["type"] = "translator_check_resp"
                    await translator.send_json_to(check)
                for _ in range(2):
                    assert (await webui.receive_json_from())["type"] == "wui_check_resp"
                assert await webui.receive_nothing()
        finally:
            await webui.disconnect()

    async def test_linking_in_admin_syncs_active_entries(self):
        """Ensure linking/unlinking a translator to an action sends/withdraws the active entries."""
        async with get_communicators(["gobgp", "frr"], [True, True]) as [
            (gobgp, _),
            (frr, _),
        ]:
            await self.api_create_entry("192.0.2.6/32")
            assert await gobgp.receive_json_from() == add_msg("192.0.2.6/32")

            await self.link_in_admin(self.gobgp, self.frr)
            assert await frr.receive_json_from() == add_msg("192.0.2.6/32")
            assert await gobgp.receive_nothing()

            await self.link_in_admin(self.gobgp)
            assert await frr.receive_json_from() == remove_msg("192.0.2.6/32")
            assert await gobgp.receive_nothing()

    async def test_deleting_translator_type_in_admin_withdraws_its_routes(self):
        """Ensure that deleting a translator type sends remove messages first so nothing is left announced."""
        async with get_communicators(["gobgp", "frr"], [True, True]) as [
            (gobgp, _),
            (frr, _),
        ]:
            await self.link_in_admin(self.gobgp, self.frr)
            await self.api_create_entry("192.0.2.7/32")
            await gobgp.receive_json_from()
            await frr.receive_json_from()

            response = await sync_to_async(self.client.post)(
                reverse("admin:route_manager_translatortype_changelist"),
                {
                    "action": "delete_selected",
                    "_selected_action": [self.frr.pk],
                    "post": "yes",
                },
            )
            assert response.status_code == status.HTTP_302_FOUND
            assert await frr.receive_json_from() == remove_msg("192.0.2.7/32")
            assert await gobgp.receive_nothing()

            response = await sync_to_async(self.client.post)(
                reverse(
                    "admin:route_manager_translatortype_delete", args=[self.gobgp.pk]
                ),
                {"post": "yes"},
            )
            assert response.status_code == status.HTTP_302_FOUND
            assert await gobgp.receive_json_from() == remove_msg("192.0.2.7/32")
            assert await frr.receive_nothing()
            assert not await sync_to_async(TranslatorType.objects.exists)()

    async def test_connect_replays_only_this_translator_types_entries(self):
        """Ensure that on connect, gobgp gets block's active entries but not rtbh's, which belong to frr."""

        def make_entries():
            rtbh = ActionType.objects.create(name="rtbh")
            rtbh.translator_types.set([self.frr])
            Entry.objects.create(
                route=Route.objects.create(route="192.0.2.4/32"),
                actiontype=self.actiontype,
            )
            Entry.objects.create(
                route=Route.objects.create(route="198.51.100.4/32"), actiontype=rtbh
            )

        await sync_to_async(make_entries)()
        gobgp = WebsocketCommunicator(router, "/ws/route_manager/translator_gobgp/")
        try:
            connected, _ = await gobgp.connect()
            assert connected
            await wait_for_connect(gobgp)
            assert await gobgp.receive_json_from() == add_msg("192.0.2.4/32")
            assert await gobgp.receive_nothing()
        finally:
            await gobgp.disconnect()

    async def test_unknown_translator_type_is_rejected(self):
        """Ensure that a typo in SCRAM_EVENTS_URL fails loudly instead of listening on an empty group."""
        translator = WebsocketCommunicator(router, "/ws/route_manager/translator_nope/")
        try:
            connected, _ = await translator.connect()
            assert connected
            closed = await translator.receive_output()
            assert closed["type"] == "websocket.close"
            assert closed["code"] == UNKNOWN_TRANSLATOR_TYPE
            assert "'nope'" in closed["reason"]
        finally:
            await translator.disconnect()
