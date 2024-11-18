"""Define tests for the URL resolution for the Users application."""

import pytest
from django.urls import resolve, reverse

from scram.users.models import User

pytestmark = pytest.mark.django_db


def test_detail(user: User):
    """Ensure we can get the URL to view details about a single User."""
    assert reverse("users:detail", kwargs={"username": user.username}) == f"/users/{user.username}/"
    assert resolve(f"/users/{user.username}/").view_name == "users:detail"


def test_update():
    """Ensure we can get the URL to update a User."""
    assert reverse("users:update") == "/users/~update/"
    assert resolve("/users/~update/").view_name == "users:update"


def test_redirect():
    """Ensure we can get the URL to redirect to a User."""
    assert reverse("users:redirect") == "/users/~redirect/"
    assert resolve("/users/~redirect/").view_name == "users:redirect"
