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
        route1 = Route.objects.create(route="192.168.1.1")
        route2 = Route.objects.create(route="192.168.1.2")

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
        who_filter = WhoFilter(request=None, params={"who": "admin"}, model=Entry, model_admin=EntryAdmin)

        queryset = Entry.objects.all()
        filtered_queryset = who_filter.queryset(None, queryset)

        self.assertEqual(filtered_queryset.count(), 1)
        self.assertEqual(filtered_queryset.first(), self.entry1)
