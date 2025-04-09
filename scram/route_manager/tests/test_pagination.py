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

        # Action type1 entries
        created_routes = Route.objects.bulk_create([
            Route(route=self.fake.unique.ipv4_public()) for x in range(self.TEST_PAGINATION_SIZE + 3)
        ])
        entries_type1 = Entry.objects.bulk_create([
            Entry(route=route, actiontype=self.atype1, is_active=True) for route in created_routes
        ])

        # Action type2 entries
        created_routes = Route.objects.bulk_create([Route(route=self.fake.unique.ipv4_public()) for x in range(3)])
        entries_type2 = Entry.objects.bulk_create([
            Entry(route=route, actiontype=self.atype2, is_active=True) for route in created_routes
        ])

        # Inactive entries
        created_routes = Route.objects.bulk_create([Route(route=self.fake.unique.ipv4_public()) for x in range(3)])
        Entry.objects.bulk_create([
            Entry(route=route, actiontype=self.atype1, is_active=False) for route in created_routes
        ])

        # Entries for unavailable action type
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
        """Test that only entries with available action types are included."""
        self.client.login(username="testuser", password="testpass123")

        url = reverse("route_manager:entry-list")
        response = self.client.get(url)

        entries_context = response.context["entries"]

        assert entries_context[self.atype1]["total"] == len(self.entries["type1"])
        assert entries_context[self.atype2]["total"] == len(self.entries["type2"])

    @override_settings(PAGINATION_SIZE=5)
    def test_pagination(self):
        """Test pagination for different action types."""
        self.client.login(username="testuser", password="testpass123")

        url = reverse("route_manager:entry-list")

        response = self.client.get(url)
        entries_context = response.context["entries"]

        # First page should have PAGINATION_SIZE items
        assert len(entries_context[self.atype1]["objs"]) == settings.PAGINATION_SIZE
        assert entries_context[self.atype1]["page_param"] == "page_type1"
        assert str(entries_context[self.atype1]["page_number"]) == "1"

        # Small atype should have all items
        assert len(entries_context[self.atype2]["objs"]) == len(self.entries["type2"])

        # Second page
        page2_response = self.client.get(f"{url}?page_type1=2")
        page2_context = page2_response.context["entries"]

        assert str(page2_context[self.atype1]["page_number"]) == "2"
        # Second page should have 3 since we initially created entries based on pagination size + 3
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
        """Test handling multiple pagination parameters simultaneously."""
        self.client.login(username="testuser", password="testpass123")

        url = reverse("route_manager:entry-list")
        response = self.client.get(f"{url}?page_type1=2&page_type2=1")

        entries_context = response.context["entries"]

        # Each type should have its own page number
        assert str(entries_context[self.atype1]["page_number"]) == "2"
        assert str(entries_context[self.atype2]["page_number"]) == "1"

        # Check current_page_params contains both parameters
        assert "page_type1" in entries_context[self.atype1]["current_page_params"]
        assert "page_type2" in entries_context[self.atype1]["current_page_params"]
