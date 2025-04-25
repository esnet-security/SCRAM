"""Test Django Request Framework Views in the Users application."""

import pytest
from django.test import RequestFactory
from django.urls import reverse
from rest_framework.test import APIClient

from scram.users.api.views import UserViewSet
from scram.users.models import User

pytestmark = pytest.mark.django_db


class TestUserViewSet:
    """Test a couple simple View operations."""

    def test_get_queryset(self, user: User, rf: RequestFactory):
        """Ensure we can view an arbitrary URL."""
        view = UserViewSet()
        request = rf.get("/fake-url/")
        request.user = user

        view.request = request

        assert user in view.get_queryset()

    def test_me(self, user: User, rf: RequestFactory):
        """Ensure we can view info on the current user."""
        view = UserViewSet()
        request = rf.get("/fake-url/")
        request.user = user

        view.request = request

        response = view.me(request)

        assert response.data == {
            "username": user.username,
            "name": user.name,
            "url": f"http://testserver/api/v1/users/{user.username}/",
        }

    def test_user_cannot_update_name(self):
        """Test that users cannot update their name via the API."""
        client = APIClient()

        original_name = "testuser"
        test_user = User.objects.create_user(
            username=original_name,
            password="password123",
        )

        # Authenticate as this user
        client.force_authenticate(user=test_user)

        # Try to update name using PUT
        url = reverse("users:detail", kwargs={"username": test_user.username})
        update_data = {"username": "New Name"}

        client.put(url, update_data)

        # Confirm user's name wasn't changed in the database
        test_user.refresh_from_db()
        assert test_user.username == original_name
