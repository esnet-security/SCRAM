"""Test Django Request Framework Views in the Users application."""

import pytest
from django.test import RequestFactory

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
