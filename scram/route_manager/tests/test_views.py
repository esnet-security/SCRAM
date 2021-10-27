from django.conf import settings
from django.contrib.auth.models import Group
from django.test import Client, TestCase
from django.urls import resolve, reverse

from scram.route_manager.views import home_page
from scram.users.models import User


class HomePageTest(TestCase):
    def test_root_url_resolves_to_home_page_view(self):
        found = resolve("/")
        self.assertEqual(found.func, home_page)


class AuthzTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.group = Group(name=settings.SCRAM_READONLY_GROUPS)
        self.group.save()
        self.user = User.objects.create(username="user")
        self.user.groups.add(self.group)
        self.client.force_login(self.user)

    def test_unauthorized_add_entry(self):
        """ Readonly group users should not be able to add an entry"""
        response = self.client.post(
            reverse("route_manager:add"), {"route": "1.2.3.4/32", "actiontype": "block"}
        )
        self.assertEqual(response.status_code, 302)
