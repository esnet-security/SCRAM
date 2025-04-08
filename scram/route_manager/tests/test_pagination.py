"""Define simple tests for pagination."""

import pytest
from django.conf import settings
from django.test import override_settings
from django.urls import reverse
from faker import Faker
from faker.providers import internet

from scram.route_manager.models import ActionType, Entry, Route

TEST_PAGINATION_SIZE = 5


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
    fake = Faker()
    fake.add_provider(internet)

    atype1, atype2, atype3 = action_types

    # Action type1 entries
    created_routes = Route.objects.bulk_create([
        Route(route=fake.unique.ipv4_public()) for x in range(TEST_PAGINATION_SIZE + 3)
    ])
    entries_type1 = Entry.objects.bulk_create([
        Entry(route=route, actiontype=atype1, is_active=True) for route in created_routes
    ])

    # Action type2 entries
    created_routes = Route.objects.bulk_create([Route(route=fake.unique.ipv4_public()) for x in range(3)])
    entries_type2 = Entry.objects.bulk_create([
        Entry(route=route, actiontype=atype2, is_active=True) for route in created_routes
    ])

    # Inactive entries
    created_routes = Route.objects.bulk_create([Route(route=fake.unique.ipv4_public()) for x in range(3)])
    Entry.objects.bulk_create([Entry(route=route, actiontype=atype1, is_active=False) for route in created_routes])

    # Entries for unavailable action type
    created_routes = Route.objects.bulk_create([Route(route=fake.unique.ipv4_public()) for x in range(3)])
    Entry.objects.bulk_create([Entry(route=route, actiontype=atype3, is_active=False) for route in created_routes])

    return {"type1": entries_type1, "type2": entries_type2}


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
        atype1, atype2, _ = action_types

        url = reverse("route_manager:entry-list")
        response = logged_in_client.get(url)

        entries_context = response.context["entries"]

        assert entries_context[atype1]["total"] == len(entries["type1"])
        assert entries_context[atype2]["total"] == len(entries["type2"])

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

    @override_settings(PAGINATION_SIZE=TEST_PAGINATION_SIZE)
    def test_invalid_page_handling(self, logged_in_client, action_types, entries):
        """Test handling of invalid page numbers."""
        type1, _, _ = action_types

        url = reverse("route_manager:entry-list")

        response = logged_in_client.get(f"{url}?page_type1=999")
        entries_context = response.context["entries"]

        # Should default to page 1
        assert entries_context[type1]["objs"].number == 1

    def test_multiple_page_parameters(self, logged_in_client, action_types, entries):
        """Test handling multiple pagination parameters simultaneously."""
        type1, type2, _ = action_types

        url = reverse("route_manager:entry-list")

        # Multiple page parameters
        response = logged_in_client.get(f"{url}?page_type1=2&page_type2=1")
        entries_context = response.context["entries"]

        # Each type should have its own page number
        assert str(entries_context[type1]["page_number"]) == "2"
        assert str(entries_context[type2]["page_number"]) == "1"

        # Check current_page_params contains both parameters
        assert "page_type1" in entries_context[type1]["current_page_params"]
        assert "page_type2" in entries_context[type1]["current_page_params"]
