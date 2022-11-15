from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class TestAddRemoveIP(APITestCase):
    def setUp(self):
        self.url = reverse("api:v1:entry-list")
        self.superuser = get_user_model().objects.create_superuser(
            "admin", "admin@es.net", "admintestpassword"
        )
        self.client.login(username="admin", password="admintestpassword")

    def test_block_ipv4(self):
        response = self.client.post(
            self.url, {"route": "1.2.3.4", "comment": "test"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_block_duplicate_ipv4(self):
        self.client.post(
            self.url, {"route": "1.2.3.4", "comment": "test"}, format="json"
        )
        response = self.client.post(
            self.url, {"route": "1.2.3.4", "comment": "test"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_block_ipv6(self):
        response = self.client.post(
            self.url, {"route": "1::", "comment": "test"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_block_duplicate_ipv6(self):
        self.client.post(self.url, {"route": "1::", "comment": "test"}, format="json")
        response = self.client.post(
            self.url, {"route": "1::", "comment": "test"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class TestUnauthenticatedAccess(APITestCase):
    def setUp(self):
        self.entry_url = reverse("api:v1:entry-list")
        self.ignore_url = reverse("api:v1:ignoreentry-list")

    def test_unauthenticated_users_have_no_create_access(self):
        response = self.client.post(self.entry_url, {"entry": "1.2.3.4"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_users_have_no_ignore_create_access(self):
        response = self.client.post(
            self.ignore_url, {"entry": "1.2.3.4"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_users_have_no_list_access(self):
        response = self.client.get(self.entry_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
