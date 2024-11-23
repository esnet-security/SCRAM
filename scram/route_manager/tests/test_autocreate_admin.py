"""This file contains tests for the auto-creation of an admin user."""

import pytest
from django.contrib.messages import get_messages
from django.test import Client
from django.urls import reverse

from scram.users.models import User


@pytest.mark.django_db
def test_autocreate_admin(settings):
    """Test that an admin user is auto-created when AUTOCREATE_ADMIN is True."""
    settings.AUTOCREATE_ADMIN = True
    client = Client()
    response = client.get(reverse("route_manager:home"))
    assert response.status_code == 200
    assert User.objects.count() == 1
    user = User.objects.get(username="admin")
    assert user.is_superuser
    assert user.email == "admin@example.com"
    messages = list(get_messages(response.wsgi_request))
    assert len(messages) == 2
    assert messages[0].level == 25  # SUCCESS
    assert messages[1].level == 20  # INFO


@pytest.mark.django_db
def test_autocreate_admin_disabled(settings):
    """Test that an admin user is not auto-created when AUTOCREATE_ADMIN is False."""
    settings.AUTOCREATE_ADMIN = False
    client = Client()
    response = client.get(reverse("route_manager:home"))
    assert response.status_code == 200
    assert User.objects.count() == 0


@pytest.mark.django_db
def test_autocreate_admin_existing_user(settings):
    """Test that an admin user is not auto-created when an existing user is present."""
    settings.AUTOCREATE_ADMIN = True
    User.objects.create_user("testuser", "test@example.com", "password")
    client = Client()
    response = client.get(reverse("route_manager:home"))
    assert response.status_code == 200
    assert User.objects.count() == 1
    assert not User.objects.filter(username="admin").exists()
