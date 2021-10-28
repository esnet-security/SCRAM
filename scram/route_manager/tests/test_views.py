from django.contrib.auth.models import Permission
from django.test import Client, TestCase
from django.urls import resolve, reverse

from scram.route_manager.models import Entry
from scram.route_manager.views import home_page
from scram.users.models import User


class HomePageTest(TestCase):
    def test_root_url_resolves_to_home_page_view(self):
        found = resolve("/")
        self.assertEqual(found.func, home_page)
