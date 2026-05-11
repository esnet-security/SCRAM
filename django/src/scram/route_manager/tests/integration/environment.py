"""Setup the environment for integration tests."""
# Note: this kinda abuses behave as just a generic test runner, but it works for now.

from django.contrib.auth import get_user_model

from scram.route_manager.models import (
    ActionType,
    Entry,
    HistoricalEntry,
    Route,
    WebSocketMessage,
    WebSocketSequenceElement,
)
from scram.route_manager.models import (
    Client as DjangoClient,
)

TEST_USER_USERNAME = "user"
TEST_USER_PASSWORD = "password"  # noqa: S105 #gitleaks: allow
TEST_CLIENT_UUID = "0e7e1cbd-7d73-4968-bc4b-ce3265dc2fd3"
TEST_CLIENT_HOSTNAME = "authorized_client.es.net"


def before_feature(context, feature):
    """Clean up database and setup test user and client."""
    user_model = get_user_model()

    # Cleanup any data related to what integration tests will create to avoid conflicts.
    Entry.objects.all().delete()
    Route.objects.all().delete()
    HistoricalEntry.objects.all().delete()
    WebSocketSequenceElement.objects.all().delete()
    WebSocketMessage.objects.all().delete()

    # Create test user
    user, _ = user_model.objects.get_or_create(
        username=TEST_USER_USERNAME,
    )
    user.set_password(TEST_USER_PASSWORD)
    user.save()

    # Create test client with authorization to block (reused across tests)
    client, _ = DjangoClient.objects.update_or_create(
        uuid=TEST_CLIENT_UUID,
        defaults={
            "client_name": TEST_CLIENT_HOSTNAME,
            "is_authorized": True,
        },
    )
    action_type, _ = ActionType.objects.get_or_create(name="block")
    client.authorized_actiontypes.clear()
    client.authorized_actiontypes.add(action_type)


def after_feature(context, feature):
    """Cleanup test data related to what we created during tests."""
    Entry.objects.all().delete()
    Route.objects.all().delete()
    HistoricalEntry.objects.all().delete()
    WebSocketSequenceElement.objects.all().delete()
    WebSocketMessage.objects.all().delete()
