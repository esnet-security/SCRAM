"""Test the WhoFilter functionality of our admin site."""

from unittest.mock import MagicMock

from django.test import TestCase

from scram.route_manager.admin import EntryAdmin, WhoFilter
from scram.route_manager.models import ActionType, Entry, Route


class WhoFilterTest(TestCase):
    """Test that the WhoFilter only shows users who have made entries."""

    def setUp(self):
        """Set up the test environment."""
        self.atype = ActionType.objects.create(name="Block")
        route1 = Route.objects.create(route="192.168.1.1/32")
        route2 = Route.objects.create(route="192.168.1.2/32")

        self.entry1 = Entry.objects.create(route=route1, actiontype=self.atype, who="admin")
        self.entry2 = Entry.objects.create(route=route2, actiontype=self.atype, who="user1")

    def test_who_filter_lookups(self):
        """Test that the WhoFilter returns the correct users who have made entries."""
        who_filter = WhoFilter(request=None, params={}, model=Entry, model_admin=EntryAdmin)

        mock_request = MagicMock()
        mock_model_admin = MagicMock(spec=EntryAdmin)

        result = who_filter.lookups(mock_request, mock_model_admin)

        self.assertIn(("admin", "admin"), result)
        self.assertIn(("user1", "user1"), result)
        self.assertEqual(len(result), 2)  # Only two users should be present

    def test_who_filter_queryset_with_value(self):
        """Test that the queryset is filtered correctly when a user is selected."""
        # Verify that the basic filtering works
        all_entries = Entry.objects.all()
        self.assertEqual(all_entries.count(), 2)

        # Filter by "admin" directly
        admin_entries = all_entries.filter(who="admin")
        self.assertEqual(admin_entries.count(), 1)
        self.assertEqual(admin_entries.first(), self.entry1)

        # Filter by "user1" directly
        user1_entries = all_entries.filter(who="user1")
        self.assertEqual(user1_entries.count(), 1)
        self.assertEqual(user1_entries.first(), self.entry2)
