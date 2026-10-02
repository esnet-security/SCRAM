"""Test our admin site customizations."""

from unittest.mock import MagicMock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from scram.route_manager.admin import EntryAdmin, WhoFilter
from scram.route_manager.models import ActionType, Entry, Route, TranslatorType


class ActionTypeAdminTest(TestCase):
    """Actiontypes with no translator types have a warning, and names can't change once created."""

    warning = "No translator types are linked to filter"

    def setUp(self):
        """Log in as admin."""
        self.client.force_login(
            get_user_model().objects.create_superuser(
                "admin", "admin@example.net", "password"
            )
        )
        self.gobgp, _ = TranslatorType.objects.get_or_create(name="gobgp")

    def add_actiontype(self, **data):
        """Submit the admin's add form for a new actiontype."""
        return self.client.post(
            reverse("admin:route_manager_actiontype_add"),
            {"name": "filter", "payload": "{}", **data},
            follow=True,
        )

    def test_actiontype_without_translator_types_warns(self):
        """Actions without translator types are saved, but there is a warning."""
        self.assertContains(self.add_actiontype(), self.warning)
        self.assertTrue(ActionType.objects.filter(name="filter").exists())

    def test_actiontype_with_a_translator_type_does_not_warn(self):
        """Ensure when we link a translator there is no warning."""
        self.assertNotContains(
            self.add_actiontype(translator_types=[self.gobgp.pk]), self.warning
        )

    def test_name_is_read_only_once_created(self):
        """Ensure you can't rename an actiontype after creation."""
        actiontype = ActionType.objects.create(name="filter")
        add_page = self.client.get(reverse("admin:route_manager_actiontype_add"))
        change_page = self.client.get(
            reverse("admin:route_manager_actiontype_change", args=[actiontype.pk])
        )
        self.assertContains(add_page, 'name="name"')
        self.assertNotContains(change_page, 'name="name"')


class TranslatorTypeAdminTest(TestCase):
    """Translator type names have to be compatible with channels group names."""

    def setUp(self):
        """Log in as admin."""
        self.client.force_login(
            get_user_model().objects.create_superuser(
                "admin", "admin@example.net", "password"
            )
        )

    def test_non_ascii_name_is_rejected(self):
        """Channels only allows ASCII group names, so a translator could never join one named like this."""
        response = self.client.post(
            reverse("admin:route_manager_translatortype_add"), {"name": "☕️covféfee"}
        )
        self.assertContains(response, "Use only letters, numbers, and underscores.")
        self.assertFalse(TranslatorType.objects.filter(name="☕️covféfee").exists())


class WhoFilterTest(TestCase):
    """Test that the WhoFilter only shows users who have made entries."""

    def setUp(self):
        """Set up the test environment."""
        self.atype = ActionType.objects.create(name="Block")
        route1 = Route.objects.create(route="192.168.1.1")
        route2 = Route.objects.create(route="192.168.1.2")

        self.entry1 = Entry.objects.create(
            route=route1, actiontype=self.atype, who="admin"
        )
        self.entry2 = Entry.objects.create(
            route=route2, actiontype=self.atype, who="user1"
        )

    def test_who_filter_lookups(self):
        """Test that the WhoFilter returns the correct users who have made entries."""
        who_filter = WhoFilter(
            request=None, params={}, model=Entry, model_admin=EntryAdmin
        )

        mock_request = MagicMock()
        mock_model_admin = MagicMock(spec=EntryAdmin)

        result = who_filter.lookups(mock_request, mock_model_admin)

        self.assertIn(("admin", "admin"), result)
        self.assertIn(("user1", "user1"), result)
        self.assertEqual(len(result), 2)  # Only two users should be present

    def test_who_filter_queryset_with_value(self):
        """Test that the queryset is filtered correctly when a user is selected."""
        who_filter = WhoFilter(
            request=None, params={"who": ["admin"]}, model=Entry, model_admin=EntryAdmin
        )

        queryset = Entry.objects.all()
        filtered_queryset = who_filter.queryset(None, queryset)

        self.assertEqual(filtered_queryset.count(), 1)
        self.assertEqual(filtered_queryset.first(), self.entry1)
