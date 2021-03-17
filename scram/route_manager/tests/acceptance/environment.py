from scram.users.tests.factories import UserFactory
from rest_framework.test import APIClient


def django_ready(context):
    # Create a user
    UserFactory(username='user', password='password')

    # Default to using the API client.
    context.test.client = APIClient()
