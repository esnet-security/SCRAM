from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class TestAddRemoveIP(APITestCase):

    def setUp(self):
        self.url = reverse('api:entry-list')
        self.superuser = get_user_model().objects.create_superuser('sam', 'sam@es.net', 'samtestpassword')
        self.client.login(username='sam', password='samtestpassword')

    def test_block_ipv4(self):
        response = self.client.post(self.url, {'route': '1.2.3.4'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_block_duplicate_ipv4(self):
        self.client.post(self.url, {'route': '1.2.3.4'}, format='json')
        response = self.client.post(self.url, {'route': '1.2.3.4'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_block_ipv6(self):
        response = self.client.post(self.url, {'route': '1::'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_block_duplicate_ipv6(self):
        self.client.post(self.url, {'route': '1::'}, format='json')
        response = self.client.post(self.url, {'route': '1::'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class TestUnauthenticatedAccess(APITestCase):

    def setUp(self):
        self.url = reverse('api:entry-list')

    def test_unauthenticated_users_have_no_create_access(self):
        response = self.client.post(self.url, {'entry': '1.2.3.4'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_users_have_no_list_access(self):
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
