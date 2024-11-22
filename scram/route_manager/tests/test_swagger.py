import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_swagger_api(client):
    """Test that the Swagger API endpoint returns a successful response."""

    url = reverse("swagger-ui")
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_swagger_api_entry_list(client):
    """Test that the Swagger API endpoint for the entry list returns a successful response."""

    url = reverse("swagger-ui") + "?url=/api/v1/entry-list"
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_swagger_api_entry_detail(client):
    """Test that the Swagger API endpoint for an entry detail returns a successful response."""

    url = reverse("swagger-ui") + "?url=/api/v1/entry-detail/1"
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_swagger_api_ignore_entry_list(client):
    """Test that the Swagger API endpoint for the ignore entry list returns a successful response."""

    url = reverse("swagger-ui") + "?url=/api/v1/ignoreentry-list"
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_swagger_api_ignore_entry_detail(client):
    """Test that the Swagger API endpoint for an ignore entry detail returns a successful response."""

    url = reverse("swagger-ui") + "?url=/api/v1/ignoreentry-detail/1"
    response = client.get(url)
    assert response.status_code == 200
