"""Define tests for authorization and permissions."""

from django.conf import settings
from django.contrib.auth.models import Group
from django.test import Client, TestCase
from django.urls import reverse

from scram.route_manager.authentication_backends import ESnetAuthBackend
from scram.route_manager.models import Client as ClientModel
from scram.route_manager.models import Entry
from scram.users.models import User


class AuthzTest(TestCase):
    """Define tests using the built-in authentication."""

    def setUp(self):
        """Define several users for our tests."""
        self.client = Client()
        self.unauthorized_user = User.objects.create(username="unauthorized")

        self.readonly_group = Group.objects.get(name="readonly")
        self.readonly_user = User.objects.create(username="readonly")
        self.readonly_user.groups.set([self.readonly_group])
        self.readonly_user.save()

        self.readwrite_group = Group.objects.get(name="readwrite")
        self.readwrite_user = User.objects.create(username="readwrite")
        self.readwrite_user.groups.set([self.readwrite_group])
        self.readwrite_user.save()

        self.admin_user = User.objects.create(username="admin", is_staff=True, is_superuser=True)

        self.write_blocked_users = [None, self.unauthorized_user, self.readonly_user]
        self.write_allowed_users = [self.readwrite_user, self.admin_user]

        self.detail_blocked_users = [None, self.unauthorized_user]
        self.detail_allowed_users = [
            self.readonly_user,
            self.readwrite_user,
            self.admin_user,
        ]

        self.authorized_client = ClientModel.objects.create(
            hostname="authorized_client.es.net",
            uuid="0e7e1cbd-7d73-4968-bc4b-ce3265dc2fd3",
            is_authorized=True,
        )
        self.authorized_client.authorized_actiontypes.set([1])

        self.unauthorized_client = ClientModel.objects.create(
            hostname="unauthorized_client.es.net",
            uuid="91e134a5-77cf-4560-9797-6bbdbffde9f8",
        )

    def create_entry(self):
        """Ensure the admin user can create an Entry."""
        self.client.force_login(self.admin_user)
        self.client.post(
            reverse("route_manager:add"),
            {
                "route": "192.0.2.199/32",
                "actiontype": "block",
                "comment": "create entry",
                "uuid": "0e7e1cbd-7d73-4968-bc4b-ce3265dc2fd3",
            },
        )
        self.client.logout()
        return Entry.objects.latest("id").id

    def test_unauthorized_add_entry(self):
        """Unauthorized users should not be able to add an Entry."""
        for user in self.write_blocked_users:
            if user:
                self.client.force_login(user)
            response = self.client.post(
                reverse("route_manager:add"),
                {
                    "route": "192.0.2.4/32",
                    "actiontype": "block",
                    "uuid": "0e7e1cbd-7d73-4968-bc4b-ce3265dc2fd3",
                },
            )
            self.assertEqual(response.status_code, 302)

    def test_authorized_add_entry(self):
        """Test authorized users with various permissions to ensure they can add an Entry."""
        for user in self.write_allowed_users:
            self.client.force_login(user)
            response = self.client.post(
                reverse("route_manager:add"),
                {
                    "route": "192.0.2.4/32",
                    "actiontype": "block",
                    "uuid": "0e7e1cbd-7d73-4968-bc4b-ce3265dc2fd3",
                },
            )
            self.assertEqual(response.status_code, 200)

    def test_unauthorized_detail_view(self):
        """Ensure that unauthorized users can't view the blocked IPs."""
        pk = self.create_entry()

        for user in self.detail_blocked_users:
            if user:
                self.client.force_login(user)
            response = self.client.get(reverse("route_manager:detail", kwargs={"pk": pk}))
            self.assertIn(response.status_code, [302, 403], msg=f"username={user}")

    def test_authorized_detail_view(self):
        """Test authorized users with various permissions to ensure they can view block details."""
        pk = self.create_entry()

        for user in self.detail_allowed_users:
            self.client.force_login(user)
            response = self.client.get(reverse("route_manager:detail", kwargs={"pk": pk}))
            self.assertEqual(response.status_code, 200, msg=f"username={user}")

    def test_unauthorized_after_group_removal(self):
        """The user has r/w access, then when we remove them from the r/w group, they no longer do."""
        test_user = User.objects.create(username="tmp_readwrite")
        test_user.groups.set([self.readwrite_group])
        test_user.save()

        self.client.force_login(test_user)
        response = self.client.post(reverse("route_manager:add"), {"route": "192.0.2.4/32", "actiontype": "block"})
        self.assertEqual(response.status_code, 200)

        test_user.groups.set([])

        response = self.client.post(reverse("route_manager:add"), {"route": "192.0.2.5/32", "actiontype": "block"})
        self.assertEqual(response.status_code, 302)


class ESnetAuthBackendTest(TestCase):
    """Define tests using OIDC authentication with our ESnetAuthBackend."""

    def setUp(self):
        """Create a sample OIDC user."""
        self.client = Client()
        self.claims = {
            "given_name": "Edward",
            "family_name": "Scissorhands",
            "preferred_username": "eddy",
            "groups": [],
        }

    def test_unauthorized(self):
        """A user with no groups should have no access."""
        claims = dict(self.claims)
        user = ESnetAuthBackend().create_user(claims)

        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(list(user.user_permissions.all()), [])

    def test_readonly(self):
        """Test r/o groups."""
        claims = dict(self.claims)
        claims["groups"] = [settings.SCRAM_READONLY_GROUPS[0]]
        user = ESnetAuthBackend().create_user(claims)

        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.has_perm("route_manager.view_entry"))
        self.assertFalse(user.has_perm("route_manager.add_entry"))

    def test_readwrite(self):
        """Test r/w groups."""
        claims = dict(self.claims)
        claims["groups"] = [settings.SCRAM_READWRITE_GROUPS[0]]
        user = ESnetAuthBackend().create_user(claims)

        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

        self.assertTrue(user.has_perm("route_manager.view_entry"))
        self.assertTrue(user.has_perm("route_manager.add_entry"))

    def test_admin(self):
        """Test admin_groups."""
        claims = dict(self.claims)
        claims["groups"] = [settings.SCRAM_ADMIN_GROUPS[0]]
        user = ESnetAuthBackend().create_user(claims)

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.has_perm("route_manager.view_entry"))
        self.assertTrue(user.has_perm("route_manager.add_entry"))

    def test_authorized_removal(self):
        """Have an authorized user, then downgrade them and make sure they're unauthorized."""
        claims = dict(self.claims)
        claims["groups"] = [settings.SCRAM_ADMIN_GROUPS[0]]
        user = ESnetAuthBackend().create_user(claims)
        pk = user.pk

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.has_perm("route_manager.view_entry"))
        self.assertTrue(user.has_perm("route_manager.add_entry"))

        claims["groups"] = [settings.SCRAM_READWRITE_GROUPS[0]]
        ESnetAuthBackend().update_user(user, claims)

        # Bypass cache
        user = User.objects.get(pk=pk)

        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.has_perm("route_manager.view_entry"))
        self.assertTrue(user.has_perm("route_manager.add_entry"))

        claims["groups"] = [settings.SCRAM_READONLY_GROUPS[0]]
        ESnetAuthBackend().update_user(user, claims)

        # Bypass cache
        user = User.objects.get(pk=pk)

        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.has_perm("route_manager.view_entry"))
        self.assertFalse(user.has_perm("route_manager.add_entry"))

        claims["groups"] = [settings.SCRAM_DENIED_GROUPS[0]]
        ESnetAuthBackend().update_user(user, claims)

        # Bypass cache
        user = User.objects.get(pk=pk)

        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.has_perm("route_manager.view_entry"))
        self.assertFalse(user.has_perm("route_manager.add_entry"))

    def test_disabled(self):
        """Pass all the groups, user should be disabled as it takes precedence."""
        claims = dict(self.claims)
        claims["groups"] = settings.SCRAM_GROUPS
        user = ESnetAuthBackend().create_user(claims)

        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.has_perm("route_manager.view_entry"))
        self.assertFalse(user.has_perm("route_manager.add_entry"))
