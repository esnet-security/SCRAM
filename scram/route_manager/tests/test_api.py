"""Use pytest to unit test the API."""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from scram.route_manager.models import ActionType, Client


class TestAddRemoveIP(APITestCase):
    """Ensure that we can block IPs, and that duplicate blocks don't generate an error."""

    def setUp(self):
        """Set up the environment for our tests."""
        self.url = reverse("api:v1:entry-list")
        self.superuser = get_user_model().objects.create_superuser("admin", "admin@es.net", "admintestpassword")
        self.client.login(username="admin", password="admintestpassword")

        # Create the ActionType
        self.actiontype, _ = ActionType.objects.get_or_create(name="block")

        self.authorized_client = Client.objects.create(
            hostname="authorized_client.es.net",
            uuid="0e7e1cbd-7d73-4968-bc4b-ce3265dc2fd3",
            is_authorized=True,
        )
        self.authorized_client.authorized_actiontypes.set([self.actiontype])

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

        # Create the ActionType that the API endpoint will try to look up
        ActionType.objects.get_or_create(name="block")

    def test_unauthenticated_users_have_no_create_access(self):
        """Ensure an unauthenticated client can't add an Entry."""
        response = self.client.post(
            self.entry_url,
            {
                "route": "192.0.2.4",
                "comment": "test",
                "uuid": "0e7e1cbd-7d73-4968-bc4b-ce3265dc2fd3",
                "who": "person",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_users_have_no_ignore_create_access(self):
        """Ensure an unauthenticated client can't add an IgnoreEntry."""
        response = self.client.post(self.ignore_url, {"route": "192.0.2.4"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_users_have_no_list_access(self):
        """Ensure an unauthenticated client can't list Entries."""
        response = self.client.get(self.entry_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
