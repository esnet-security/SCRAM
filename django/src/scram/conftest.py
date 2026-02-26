"""Some simple tests for the User app."""

import pytest

from scram.users.models import User
from scram.users.tests.factories import UserFactory


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    """Configure the test to use the temp directory."""
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user() -> User:
    """Return the UserFactory."""
    return UserFactory()
