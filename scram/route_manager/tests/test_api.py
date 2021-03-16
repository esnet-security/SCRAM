from rest_framework import status
from rest_framework.test import APITestCase

from django.contrib.auth import get_user_model
from django.urls import reverse


class TestAddRemoveIP(APITestCase):

    def setUp(self):
        self.url = reverse('route_manager:ipaddress_rest_api')
        self.superuser = get_user_model().objects.create_superuser('sam', 'sam@es.net', 'samtestpassword')
        self.client.login(username='sam', password='samtestpassword')

    def test_create_ipv4(self):
        response = self.client.post(self.url, {'ip': '1.2.3.4'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_duplicate_ipv4(self):
        self.client.post(self.url, {'ip': '1.2.3.4'}, format='json')
        response = self.client.post(self.url, {'ip': '1.2.3.4'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_ipv6(self):
        response = self.client.post(self.url, {'ip': '1::'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_duplicate_ipv6(self):
        self.client.post(self.url, {'ip': '1::'}, format='json')
        response = self.client.post(self.url, {'ip': '1::'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestUnauthenticatedAccess(APITestCase):

    def setUp(self):
        self.url = reverse('route_manager:ipaddress_rest_api')

    def test_unauthenticated_users_have_no_create_access(self):
        response = self.client.post(self.url, {'ip': '1.2.3.4'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_users_have_no_list_access(self):
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
