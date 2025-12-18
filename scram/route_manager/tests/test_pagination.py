"""Define simple tests for pagination."""

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from faker import Faker
from faker.providers import internet

from scram.route_manager.models import ActionType, Entry, Route


@pytest.mark.django_db
class TestEntriesListView(TestCase):
    """Test to make sure our pagination and related scaffolding work."""

    TEST_PAGINATION_SIZE = 5

    def setUp(self):
        """Set up the test environment."""
        self.fake = Faker()
        self.fake.add_provider(internet)
        get_user_model().objects.create_user(username="testuser", password="testpass123")

        self.atype1 = ActionType.objects.create(name="Type1", available=True)
        self.atype2 = ActionType.objects.create(name="Type2", available=True)
        self.atype3 = ActionType.objects.create(name="Type3", available=False)

        # Create enough entries to test pagination
        created_routes = Route.objects.bulk_create([
            Route(route=self.fake.unique.ipv4_public()) for x in range(self.TEST_PAGINATION_SIZE + 3)
        ])
        entries_type1 = Entry.objects.bulk_create([
            Entry(route=route, actiontype=self.atype1, is_active=True) for route in created_routes
        ])

        # Create a second type of entries to test filtering per actiontype
        created_routes = Route.objects.bulk_create([Route(route=self.fake.unique.ipv4_public()) for x in range(3)])
        entries_type2 = Entry.objects.bulk_create([
            Entry(route=route, actiontype=self.atype2, is_active=True) for route in created_routes
        ])

        # Create inactive entries to test filtering by available actiontypes
        created_routes = Route.objects.bulk_create([Route(route=self.fake.unique.ipv4_public()) for x in range(3)])
        Entry.objects.bulk_create([
            Entry(route=route, actiontype=self.atype1, is_active=False) for route in created_routes
        ])

        # Create entries for an invalid actiontype to test that
        created_routes = Route.objects.bulk_create([Route(route=self.fake.unique.ipv4_public()) for x in range(3)])
        Entry.objects.bulk_create([
            Entry(route=route, actiontype=self.atype3, is_active=False) for route in created_routes
        ])

        self.entries = {
            "type1": entries_type1,
            "type2": entries_type2,
        }

    def test_context(self):
        """Test that the context structure is correctly filled out."""
        self.client.login(username="testuser", password="testpass123")

        url = reverse("route_manager:entry-list")
        response = self.client.get(url)

        assert response.status_code == 200
        assert "entries" in response.context
        entries_context = response.context["entries"]

        assert self.atype1 in entries_context
        assert self.atype2 in entries_context
        assert self.atype3 not in entries_context

    def test_filtering_entries_by_action_type(self):
        """Test that our paginated output has entries for all available actiontypes in our paginated output."""
        self.client.login(username="testuser", password="testpass123")

        url = reverse("route_manager:entry-list")
        response = self.client.get(url)

        entries_context = response.context["entries"]

        assert entries_context[self.atype1]["total"] == len(self.entries["type1"])
        assert entries_context[self.atype2]["total"] == len(self.entries["type2"])

    @override_settings(PAGINATION_SIZE=5)
    def test_pagination(self):
        """Test pagination when there's multiple action types."""
        self.client.login(username="testuser", password="testpass123")

        url = reverse("route_manager:entry-list")

        response = self.client.get(url)
        entries_context = response.context["entries"]

        # First page should have PAGINATION_SIZE entries for actiontype with more entries than pagination size
        assert len(entries_context[self.atype1]["objs"]) == settings.PAGINATION_SIZE
        assert entries_context[self.atype1]["page_param"] == "page_type1"
        assert str(entries_context[self.atype1]["page_number"]) == "1"

        # First page should include all entries for actiontype with less entries than pagination size
        assert len(entries_context[self.atype2]["objs"]) == len(self.entries["type2"])

        # Second page should have the rest of the entries for actiontype with more entries than pagination size
        page2_response = self.client.get(f"{url}?page_type1=2")
        page2_context = page2_response.context["entries"]

        assert str(page2_context[self.atype1]["page_number"]) == "2"
        assert len(page2_context[self.atype1]["objs"]) == 3

    @override_settings(PAGINATION_SIZE=TEST_PAGINATION_SIZE)
    def test_invalid_page_handling(self):
        """Test handling of invalid page numbers."""
        self.client.login(username="testuser", password="testpass123")

        url = reverse("route_manager:entry-list")
        response = self.client.get(f"{url}?page_type1=999")

        entries_context = response.context["entries"]

        # Should default to page 1
        assert entries_context[self.atype1]["objs"].number == 1

    def test_multiple_page_parameters(self):
        """Test that we can have separate pages when we have more than one actiontype."""
        self.client.login(username="testuser", password="testpass123")

        url = reverse("route_manager:entry-list")
        response = self.client.get(f"{url}?page_type1=2&page_type2=1")

        entries_context = response.context["entries"]

        # Each type should have its own page number
        assert str(entries_context[self.atype1]["page_number"]) == "2"
        assert str(entries_context[self.atype2]["page_number"]) == "1"
        assert "page_type1" in entries_context[self.atype1]["current_page_params"]
        assert "page_type2" in entries_context[self.atype1]["current_page_params"]
