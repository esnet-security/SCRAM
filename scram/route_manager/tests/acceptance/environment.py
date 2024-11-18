"""Setup the environment for tests."""

from rest_framework.test import APIClient

from scram.users.tests.factories import UserFactory


def django_ready(context):
    """Create a user that tests can use for authenticated/unauthenticated testing."""
    # Create a user
    UserFactory(username="user", password="password")

    # Default to using the API client.
    context.test.client = APIClient()
