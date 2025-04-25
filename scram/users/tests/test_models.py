"""Define tests for the Models in the Users application."""

import pytest

from scram.users.models import User

pytestmark = pytest.mark.django_db


def test_user_get_absolute_url(user: User):
    """Ensure w ecan convert a User object into a URL with info about that user."""
    assert user.get_absolute_url() == f"/users/{user.username}/"
