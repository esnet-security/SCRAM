"""Tasks for doing scheduled things in SCRAM via the API."""

from datetime import UTC, datetime
from typing import Any

import httpx

from .app import scram_api_scheduler
from .settings import settings


@scram_api_scheduler.task
def perform_process_updates() -> dict[Any, Any]:
    """Trigger the SCRAM /process_endpoints API endpoint to process pending updates.

    Makes a GET request to the /process_updates endpoint with a timeout 5 seconds
    shorter than the process_updates_interval setting to prevent stacking up calls.

    Returns:
        dict: Response containing status and timestamp on success.
    """
    timeout = settings.process_updates_interval - 5
    with httpx.Client() as client:
        response = client.get(f"{settings.scram_api_url}process_updates/", timeout=timeout)
        response.raise_for_status()

        return {"api_response": response.json(), "status": "success", "timestamp": datetime.now(UTC).isoformat()}
