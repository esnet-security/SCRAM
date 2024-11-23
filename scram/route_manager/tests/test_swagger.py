"""Test the swagger API endpoints."""

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_swagger_api(client):
    """Test that the Swagger API endpoint returns a successful response."""
    url = reverse("swagger-ui")
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_redoc_api(client):
    """Test that the Redoc API endpoint returns a successful response."""
    url = reverse("redoc")
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_schema_api(client):
    """Test that the Schema API endpoint returns a successful response."""
    url = reverse("schema")
    response = client.get(url)
    assert response.status_code == 200
    expected_strings = [b"/entries/", b"/actiontypes/", b"/ignore_entries/", b"/users/"]
    assert all(string in response.content for string in expected_strings)
