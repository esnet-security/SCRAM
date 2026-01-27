"""Tests for scheduler settings."""

import os

import pytest
from pydantic import ValidationError
from scheduler.settings import Settings


class TestSettingsValidation:
    """Test Settings validation."""

    def test_valid_settings(self):
        """Make sure valid settings load without error."""
        settings = Settings(
            celery_broker_url="redis://localhost:6379/0",
            celery_result_backend="redis://localhost:6379/1",
            scram_api_url="http://localhost:8000/api/",
            process_updates_interval=30,
            process_updates_timeout_offset=1,
        )
        assert settings.celery_broker_url == "redis://localhost:6379/0"
        assert settings.celery_result_backend == "redis://localhost:6379/1"
        assert settings.scram_api_url == "http://localhost:8000/api/"
        assert settings.process_updates_interval == 30
        assert settings.process_updates_timeout_offset == 1

    def test_missing_required_fields(self):
        """Make sure missing required fields raise a ValidationError from pydantic-settings."""
        # Unset required environment variables and try to instantiate settings.
        saved_broker = os.environ.pop("CELERY_BROKER_URL", None)
        saved_backend = os.environ.pop("CELERY_RESULT_BACKEND", None)
        saved_api = os.environ.pop("SCRAM_API_URL", None)
        try:
            with pytest.raises(ValidationError):
                Settings(
                    celery_broker_url="redis://localhost:6379/0",
                )
        finally:
            # Restore environment variables back to what they were
            if saved_broker:
                os.environ["CELERY_BROKER_URL"] = saved_broker
            if saved_backend:
                os.environ["CELERY_RESULT_BACKEND"] = saved_backend
            if saved_api:
                os.environ["SCRAM_API_URL"] = saved_api

    def test_interval_greater_than_timeout(self):
        """Make sure that our update interval validation works when interval < timeout."""
        with pytest.raises(
            ValueError, match="must be greater than process_updates_timeout_offset"
        ):
            Settings(
                celery_broker_url="redis://localhost:6379/0",
                celery_result_backend="redis://localhost:6379/1",
                scram_api_url="http://localhost:8000/api/",
                process_updates_interval=5,
                process_updates_timeout_offset=10,  # Greater than interval
            )

    def test_interval_equal_to_timeout(self):
        """Make sure that our update interval validation works when interval == timeout."""
        with pytest.raises(
            ValueError, match="must be greater than process_updates_timeout_offset"
        ):
            Settings(
                celery_broker_url="redis://localhost:6379/0",
                celery_result_backend="redis://localhost:6379/1",
                scram_api_url="http://localhost:8000/api/",
                process_updates_interval=10,
                process_updates_timeout_offset=10,  # Equal to interval
            )
