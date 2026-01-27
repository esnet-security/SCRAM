"""Pytest configuration and fixtures for scheduler celery app."""

import os
from unittest.mock import MagicMock

import pytest

# Set mandatory environment variables
os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6379/0")
os.environ.setdefault("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
os.environ.setdefault("SCRAM_API_URL", "http://localhost:8000/api/")


@pytest.fixture
def mock_scram_process_updates():
    """Create a mock HTTP response for process_updates."""
    response = MagicMock()
    response.json.return_value = {}
    response.raise_for_status.return_value = None
    return response


@pytest.fixture
def mock_http_client(mock_scram_process_updates):
    """Create a mocked httpx.Client with a context manager."""
    client = MagicMock()
    client.get.return_value = mock_scram_process_updates
    client.__enter__.return_value = client
    client.__exit__.return_value = None
    return client
