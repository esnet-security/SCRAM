"""Use pytest to unit test the API."""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from scram.route_manager.models import ActionType, Client, Entry, Route


class TestAddRemoveIP(APITestCase):
    """Ensure that we can block IPs, and that duplicate blocks don't generate an error."""

    def setUp(self):
        """Set up the environment for our tests."""
        self.url = reverse("api:v1:entry-list")
        self.superuser = get_user_model().objects.create_superuser(
            "admin", "admin@es.net", "admintestpassword"
        )
        self.client.login(username="admin", password="admintestpassword")
        self.authorized_client = Client.objects.create(
            client_name="authorized_client.es.net",
            uuid="0e7e1cbd-7d73-4968-bc4b-ce3265dc2fd3",
            is_authorized=True,
        )
        self.authorized_client.authorized_actiontypes.set([1])

    def test_block_ipv4(self):
        """Block a v4 IP."""
        response = self.client.post(
            self.url,
            {
                "route": "192.0.2.4",
                "comment": "test",
                "uuid": "0e7e1cbd-7d73-4968-bc4b-ce3265dc2fd3",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_block_duplicate_ipv4(self):
        """Block an existing v4 IP and ensure we don't get an error."""
        self.client.post(
            self.url,
            {
                "route": "192.0.2.4",
                "comment": "test",
                "uuid": "0e7e1cbd-7d73-4968-bc4b-ce3265dc2fd3",
            },
            format="json",
        )
        response = self.client.post(
            self.url,
            {
                "route": "192.0.2.4",
                "comment": "test",
                "uuid": "0e7e1cbd-7d73-4968-bc4b-ce3265dc2fd3",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_block_ipv6(self):
        """Block a v6 IP."""
        response = self.client.post(
            self.url,
            {
                "route": "1::",
                "comment": "test",
                "uuid": "0e7e1cbd-7d73-4968-bc4b-ce3265dc2fd3",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_block_duplicate_ipv6(self):
        """Block an existing v6 IP and ensure we don't get an error."""
        self.client.post(
            self.url,
            {
                "route": "1::",
                "comment": "test",
                "uuid": "0e7e1cbd-7d73-4968-bc4b-ce3265dc2fd3",
            },
            format="json",
        )
        response = self.client.post(
            self.url,
            {
                "route": "1::",
                "comment": "test",
                "uuid": "0e7e1cbd-7d73-4968-bc4b-ce3265dc2fd3",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class TestUnauthenticatedAccess(APITestCase):
    """Ensure that an unathenticated client can't do anything."""

    def setUp(self):
        """Define some helper variables."""
        self.entry_url = reverse("api:v1:entry-list")
        self.ignore_url = reverse("api:v1:ignoreentry-list")

    def test_unauthenticated_users_have_no_create_access(self):
        """Ensure an unauthenticated client can't add an Entry."""
        response = self.client.post(
            self.entry_url,
            {
                "route": "192.0.2.4",
                "comment": "test",
                "uuid": "0e7e1cbd-7d73-4968-bc4b-ce3265dc2fd3",
                # "who": "person",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_users_have_no_ignore_create_access(self):
        """Ensure an unauthenticated client can't add an IgnoreEntry."""
        response = self.client.post(
            self.ignore_url, {"route": "192.0.2.4"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_users_have_no_list_access(self):
        """Ensure an unauthenticated client can't list Entries."""
        response = self.client.get(self.entry_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TestIsActive(APITestCase):
    """Test the is_active endpoint."""

    def setUp(self):
        """Set up test data."""
        self.url = reverse("api:v1:is_active-list")
        self.authorized_client = Client.objects.create(
            hostname="authorized_client.es.net",
            uuid="0e7e1cbd-7d73-4968-bc4b-ce3265dc2fd3",
            is_authorized=True,
        )
        self.authorized_client.authorized_actiontypes.set([1])
        self.actiontype, _ = ActionType.objects.get_or_create(pk=1, defaults={"name": "block"})

        # Create some active entries

        # Active IPv4
        route_v4 = Route.objects.create(route="192.0.2.100")
        Entry.objects.create(
            route=route_v4, is_active=True, comment="test active", who="test", actiontype=self.actiontype
        )

        # Active IPv6
        route_v6 = Route.objects.create(route="2001:db8::1")
        Entry.objects.create(
            route=route_v6, is_active=True, comment="test active v6", who="test", actiontype=self.actiontype
        )

        # Deactivated IPv4 entry
        route_inactive = Route.objects.create(route="192.0.2.200")
        Entry.objects.create(
            route=route_inactive, is_active=False, comment="inactive", who="test", actiontype=self.actiontype
        )

        # Deactived IPv6 entry
        route_inactive = Route.objects.create(route="2001:db8::5")
        Entry.objects.create(
            route=route_inactive, is_active=False, comment="inactive", who="test", actiontype=self.actiontype
        )

    def test_active_ipv4_returns_true(self):
        """Check that an active IPv4 returns is_active=true."""
        response = self.client.get(self.url, {"cidr": "192.0.2.100"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["is_active"], True)
        self.assertEqual(response.data["results"][0]["route"], "192.0.2.100/32")

    def test_active_ipv6_returns_true(self):
        """Check that an active IPv6 returns is_active=true."""
        response = self.client.get(self.url, {"cidr": "2001:db8::1"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["is_active"], True)
        self.assertEqual(response.data["results"][0]["route"], "2001:db8::1/128")

    def test_inactive_entry_ipv4_returns_false(self):
        """Check that an inactive entry returns is_active=false."""
        response = self.client.get(self.url, {"cidr": "192.0.2.200"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["is_active"], False)
        self.assertEqual(response.data["results"][0]["route"], "192.0.2.200/32")

    def test_inactive_entry_ipv6_returns_false(self):
        """Check that an inactive entry returns is_active=false."""
        response = self.client.get(self.url, {"cidr": "2001:db8::5"})
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["is_active"], False)
        self.assertEqual(response.data["results"][0]["route"], "2001:db8::5/128")

    def test_unauthenticated_access_allowed(self):
        """Ensure unauthenticated clients can check if IPs are active."""
        # Logout any authenticated user
        self.client.logout()
        response = self.client.get(self.url, {"cidr": "192.0.2.100"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["is_active"], True)
