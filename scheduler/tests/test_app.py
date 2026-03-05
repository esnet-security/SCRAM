"""Tests for scheduler app configuration."""

import importlib
import os

from scheduler.app import scram_api_scheduler
from scheduler.settings import settings


class TestCeleryApp:
    """Test Celery app configuration."""

    def test_app_settings(self):
        """Test that Celery app pulled in the correct settings."""
        assert scram_api_scheduler.conf.broker_url == settings.celery_broker_url
        assert scram_api_scheduler.conf.result_backend == settings.celery_result_backend
        assert (
            scram_api_scheduler.conf.result_expires == settings.celery_keep_results_time
        )

    def test_beat_schedule_exists(self):
        """Test that beat schedule is always configured by default to run process_updates."""
        assert "perform-process-updates" in scram_api_scheduler.conf.beat_schedule
        task_config = scram_api_scheduler.conf.beat_schedule["perform-process-updates"]
        assert task_config["task"] == "scheduler.tasks.perform_process_updates"
        assert task_config["schedule"] == settings.process_updates_interval

    def test_beat_schedule_disabled_when_disable_flag_set(self):
        """Test that process_updates beat schedule is removed when DISABLE_PROCESS_UPDATES=true.

        Kinda janky, but it works, and now we have 100% coverage.
        """
        # Set the disable env var and then reload settings, then the app.
        os.environ["DISABLE_PROCESS_UPDATES"] = "true"

        try:
            import scheduler.settings

            importlib.reload(scheduler.settings)
            import scheduler.app

            importlib.reload(scheduler.app)
            from scheduler.app import scram_api_scheduler as disabled_scheduler

            # Verify the task is NOT in the beat schedule
            assert (
                "perform-process-updates" not in disabled_scheduler.conf.beat_schedule
            )
        finally:
            # Set everything back to how it was in case we add more tests in the future.
            os.environ.pop("DISABLE_PROCESS_UPDATES", None)
            importlib.reload(scheduler.settings)
            importlib.reload(scheduler.app)
