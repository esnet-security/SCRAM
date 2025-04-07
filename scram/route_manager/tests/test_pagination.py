"""Define simple tests for pagination."""

import pytest
from django.conf import settings
from django.test import override_settings
from django.urls import reverse

from scram.route_manager.models import ActionType, Entry, Route


@pytest.fixture
def action_types():
    """Fixture to create test action types."""
    atype1 = ActionType.objects.create(name="Type1", available=True)
    atype2 = ActionType.objects.create(name="Type2", available=True)
    atype3 = ActionType.objects.create(name="Type3", available=False)

    return atype1, atype2, atype3


@pytest.fixture
def logged_in_client(client, django_user_model):
    """Fixture to create a test user and log them in."""
    django_user_model.objects.create_user(username="testuser", password="testpass123")
    client.login(username="testuser", password="testpass123")
    return client


@pytest.fixture
def entries(action_types):
    """Fixture to create test entries for different action types."""
    atype1, atype2, atype3 = action_types
    test_pagination_size = 5

    # Action type1 entries
    entries_type1 = []
    for i in range(test_pagination_size + 3):
        unique_route, _ = Route.objects.get_or_create(route=f"192.0.2.{100 + i}")
        entries_type1.append(Entry.objects.create(route=unique_route, actiontype=atype1, is_active=True))

    # Type2 entries
    entries_type2 = []
    for i in range(3):
        # Get or create a unique route for each entry
        unique_route, _ = Route.objects.get_or_create(route=f"192.0.2.{200 + i}")
        entries_type2.append(Entry.objects.create(route=unique_route, actiontype=atype2, is_active=True))

    # Some inactive entries
    inactive_route1, _ = Route.objects.get_or_create(route="192.0.2.50")
    inactive_route2, _ = Route.objects.get_or_create(route="192.0.2.51")
    Entry.objects.get_or_create(route=inactive_route1, actiontype=atype1, is_active=False)
    Entry.objects.get_or_create(route=inactive_route2, actiontype=atype2, is_active=False)

    # Entries for unavailable action type
    unavailable_route, _ = Route.objects.get_or_create(route="192.0.2.60")
    Entry.objects.get_or_create(route=unavailable_route, actiontype=atype3, is_active=True)

    return {"type1": entries_type1, "type2": entries_type2, "test_pagination_size": test_pagination_size}


@pytest.mark.django_db
class TestEntriesListView:
    """Test to make sure our pagination and related scaffolding work."""

    def test_context(self, logged_in_client, action_types, entries):
        """Test that the context structure is correctly filled out."""
        atype1, atype2, atype3 = action_types

        url = reverse("route_manager:entry-list")
        response = logged_in_client.get(url)

        assert response.status_code == 200
        assert "entries" in response.context
        entries_context = response.context["entries"]

        assert atype1 in entries_context
        assert atype2 in entries_context
        assert atype3 not in entries_context

    def test_filtering_entries_by_action_type(self, logged_in_client, action_types, entries):
        """Test that only entries with available action types are included."""
        type1, type2, _ = action_types

        url = reverse("route_manager:entry-list")
        response = logged_in_client.get(url)

        entries_context = response.context["entries"]

        # Check only active entries
        assert entries_context[type1]["total"] == len(entries["type1"])
        assert entries_context[type2]["total"] == len(entries["type2"])

    @override_settings(PAGINATION_SIZE=5)
    def test_pagination(self, logged_in_client, action_types, entries):
        """Test pagination for different action types."""
        atype1, atype2, _ = action_types

        url = reverse("route_manager:entry-list")

        response = logged_in_client.get(url)
        entries_context = response.context["entries"]

        # First page should have PAGINATION_SIZE items
        assert len(entries_context[atype1]["objs"]) == settings.PAGINATION_SIZE
        assert entries_context[atype1]["page_param"] == "page_type1"
        assert str(entries_context[atype1]["page_number"]) == "1"

        # Small atype should have all items
        assert len(entries_context[atype2]["objs"]) == len(entries["type2"])

        # Second page
        page2_response = logged_in_client.get(f"{url}?page_type1=2")
        page2_context = page2_response.context["entries"]

        assert str(page2_context[atype1]["page_number"]) == "2"
        # Second page should have 3 since we initially created entries based on pagination size + 3
        assert len(page2_context[atype1]["objs"]) == 3

    @override_settings(PAGINATION_SIZE=5)
    def test_invalid_page_handling(self, logged_in_client, action_types, entries):
        """Test handling of invalid page numbers."""
        type1, _, _ = action_types

        url = reverse("route_manager:entry-list")

        # Invalid page number
        response = logged_in_client.get(f"{url}?page_type1=999")
        entries_context = response.context["entries"]

        # Should default to page 1
        assert len(entries_context[type1]["objs"]) == settings.PAGINATION_SIZE

    def test_multiple_page_parameters(self, logged_in_client, action_types, entries):
        """Test handling multiple pagination parameters simultaneously."""
        type1, type2, _ = action_types

        url = reverse("route_manager:entry-list.")

        # Multiple page parameters
        response = logged_in_client.get(f"{url}?page_type1=2&page_type2=1")
        entries_context = response.context["entries"]

        # Each type should have its own page number
        assert str(entries_context[type1]["page_number"]) == "2"
        assert str(entries_context[type2]["page_number"]) == "1"

        # Check current_page_params contains both parameters
        assert "page_type1" in entries_context[type1]["current_page_params"]
        assert "page_type2" in entries_context[type1]["current_page_params"]
