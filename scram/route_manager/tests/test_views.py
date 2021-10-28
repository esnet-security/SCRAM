from django.test import Client, TestCase
from django.urls import resolve, reverse

from scram.route_manager.views import home_page


class HomePageTest(TestCase):
    def test_root_url_resolves_to_home_page_view(self):
        found = resolve("/")
        self.assertEqual(found.func, home_page)


class AuthzTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_unauthorized_add_entry(self):
        """ Readonly group users should not be able to add an entry"""
        url = reverse("route_manager:entry-list")
        response = self.client.get(url)
        import pdb

        pdb.set_trace()
        self.assertEqual(response.status_code, 403)
