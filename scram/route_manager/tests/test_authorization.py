from django.contrib.auth.models import Permission
from django.test import Client, TestCase
from django.urls import reverse

from scram.route_manager.authentication_backends import ESnetAuthBackend
from scram.route_manager.models import Entry
from scram.users.models import User

class AuthzTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(username="sam")
        self.view = Permission.objects.get(name="Can view entry")
        self.add = Permission.objects.get(name="Can add entry")
        self.delete = Permission.objects.get(name="Can delete entry")
        self.change = Permission.objects.get(name="Can change entry")
        self.user.user_permissions.add(self.view)
        self.user.user_permissions.add(self.add)
        self.user.user_permissions.add(self.delete)
        self.user.user_permissions.add(self.change)

    def test_unauthorized_add_entry(self):
        """ Readonly group users should not be able to add an entry"""
        response = self.client.post(
            reverse("route_manager:add"), {"route": "1.2.3.4/32", "actiontype": "block"}
        )
        self.assertEqual(response.status_code, 302)

    def test_authorized_add_entry(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("route_manager:add"), {"route": "1.2.3.4/32", "actiontype": "block"}
        )
        self.assertEqual(response.status_code, 200)

    def test_unauthorized_delete_entry(self):
        response = self.client.post(reverse("route_manager:delete", kwargs={"pk": 0}))
        self.assertEqual(response.status_code, 302)

    def test_authorized_delete_entry(self):
        self.client.force_login(self.user)
        self.client.post(
            reverse("route_manager:add"), {"route": "2.2.3.4/32", "actiontype": "block"}
        )
        pk = Entry.objects.latest("id").id
        response = self.client.post(reverse("route_manager:delete", kwargs={"pk": pk}))
        self.assertEqual(response.status_code, 302)

    def test_unauthorized_detail_view(self):
        self.client.force_login(self.user)
        self.client.post(
            reverse("route_manager:add"), {"route": "3.2.3.4/32", "actiontype": "block"}
        )
        self.client.logout()
        pk = Entry.objects.latest("id").id
        response = self.client.get(reverse("route_manager:detail", kwargs={"pk": pk}))
        self.assertEqual(response.status_code, 302)

    def test_authorized_detail_view(self):
        self.client.force_login(self.user)
        self.client.post(
            reverse("route_manager:add"), {"route": "4.2.3.4/32", "actiontype": "block"}
        )
        pk = Entry.objects.latest("id").id
        response = self.client.get(reverse("route_manager:detail", kwargs={"pk": pk}))
        self.assertEqual(response.status_code, 200)

    def test_unauthorized_after_group_removal(self):
        """The user has r/w access, then when we remove them from the r/w group, they no longer do."""

        self.test_authorized_add_entry()
        self.user.user_permissions.remove(self.add)
        self.test_unauthorized_add_entry()


class OidcTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_unauthorized(self):
        """A user with no groups should have no access"""

        claims = {"groups": []}

        user = ESnetAuthBackend().create_user(claims)
        self.assertFalse(user.is_staff)

