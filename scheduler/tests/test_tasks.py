"""Tests for scheduler tasks."""

from unittest.mock import MagicMock, patch

import httpx
import pytest
from scheduler.tasks import perform_process_updates

API_RESPONSE_EXAMPLE = {
    "entries_deleted": 0,
    "active_entries": 0,
    "entries_reprocessed": 0,
    "entries_reprocessed_list": [],
}


class TestPerformProcessUpdatesTask:
    """Tests for  the perform_process_updates task."""

    @patch("scheduler.tasks.httpx.Client")
    def test_successful_api_call(
        self, mock_client_class, mock_http_client, mock_scram_process_updates
    ):
        """Test that a successful API call returns the expected structure."""
        mock_scram_process_updates.json.return_value = API_RESPONSE_EXAMPLE
        mock_client_class.return_value = mock_http_client

        result = perform_process_updates()

        assert result["status"] == "success"
        assert result["api_response"] == API_RESPONSE_EXAMPLE
        assert "timestamp" in result

    @patch("scheduler.tasks.httpx.Client")
    def test_timeout_calculation(self, mock_client_class, mock_http_client):
        """Test that our timeout value is correctly calculated."""
        mock_client_class.return_value = mock_http_client

        perform_process_updates()

        # Look into the mock to see how our httpx client was called; since our setting
        # file's defaults are 30 for polling and 1 for the timeout delta, timeout should be 29
        call_kwargs = mock_http_client.get.call_args[1]
        assert call_kwargs["timeout"] == 29

    @patch("scheduler.tasks.httpx.Client")
    def test_http_error_propagates(
        self, mock_client_class, mock_http_client, mock_scram_process_updates
    ):
        """Test that we aren't catching HTTP errors and are letting them bubble up to the celery task for logging."""
        mock_scram_process_updates.raise_for_status.side_effect = httpx.HTTPStatusError(
            "400 Bad Request", request=MagicMock(), response=MagicMock()
        )
        mock_client_class.return_value = mock_http_client

        with pytest.raises(httpx.HTTPStatusError):
            perform_process_updates()
