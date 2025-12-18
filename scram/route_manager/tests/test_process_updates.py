"""Unit tests for process_updates syncing logic."""

from datetime import UTC, datetime, timedelta

import pytest
from django.conf import settings

from scram.route_manager.models import ActionType, Entry, Route, WebSocketMessage, WebSocketSequenceElement
from scram.route_manager.views import check_for_orphaned_history, get_entries_to_process


@pytest.fixture
def actiontype(db):
    """Create a block actiontype for tests."""
    return ActionType.objects.create(name="block")


@pytest.fixture
def websocket_config(actiontype):
    """Create the WebSocket configuration needed for reprocess_entries."""
    wsm = WebSocketMessage.objects.create(
        msg_type="translator_add",
        msg_data_route_field="route",
        msg_data={"route": "placeholder"},
    )
    WebSocketSequenceElement.objects.create(
        websocketmessage=wsm,
        action_type=actiontype,
        verb="A",
        order_num=1,
    )
    return wsm


@pytest.fixture
def other_instance():
    """Return a hostname different from the current instance."""
    return "scram2.example.com"


@pytest.fixture
def current_instance():
    """Return the current SCRAM hostname."""
    return settings.SCRAM_HOSTNAME


def create_entry(actiontype, ip, instance, is_active=True, **kwargs):
    """Helper to create an entry with the given parameters."""
    route = Route.objects.create(route=ip)
    return Entry.objects.create(
        route=route,
        actiontype=actiontype,
        is_active=is_active,
        who="test",
        comment="test entry",
        originating_scram_instance=instance,
        **kwargs,
    )


class TestGetEntriesToProcess:
    """Tests for get_entries_to_process()."""

    def test_empty_when_no_entries(self, db):
        """Returns empty list when no entries exist."""
        cutoff = datetime.now(UTC) - timedelta(minutes=2)
        assert get_entries_to_process(cutoff) == []

    def test_finds_entry_from_other_instance(self, actiontype, other_instance):
        """Finds entries created by other SCRAM instances."""
        entry = create_entry(actiontype, "192.0.2.1/32", other_instance)
        cutoff = datetime.now(UTC) - timedelta(minutes=2)

        result = get_entries_to_process(cutoff)

        assert len(result) == 1
        assert result[0].id == entry.id

    def test_excludes_current_instance_entries(self, actiontype, current_instance):
        """Does not return entries from the current SCRAM instance."""
        create_entry(actiontype, "192.0.2.2/32", current_instance)
        cutoff = datetime.now(UTC) - timedelta(minutes=2)

        result = get_entries_to_process(cutoff)

        assert result == []

    def test_finds_modified_entries(self, actiontype, other_instance):
        """Finds entries modified after creation (uses history tracking)."""
        entry = create_entry(actiontype, "192.0.2.3/32", other_instance)

        # Set cutoff after creation, then modify
        cutoff = datetime.now(UTC)
        entry.comment = "modified"
        entry.save()

        result = get_entries_to_process(cutoff)

        assert len(result) == 1
        assert result[0].comment == "modified"

    def test_finds_soft_deleted_entries(self, actiontype, other_instance):
        """Finds entries that were deactivated (expiration, by hand, etc.)."""
        entry = create_entry(actiontype, "192.0.2.4/32", other_instance)
        cutoff = datetime.now(UTC)

        entry.is_active = False
        entry.save()

        result = get_entries_to_process(cutoff)

        assert len(result) == 1
        assert result[0].is_active is False

    def test_respects_cutoff_time(self, actiontype, other_instance):
        """Only returns entries modified after the cutoff time by faking the modified time."""
        old_entry = create_entry(actiontype, "192.0.2.5/32", other_instance)

        # Backdate the history
        history = old_entry.history.latest()
        history.history_date = datetime.now(UTC) - timedelta(minutes=5)
        history.save()

        cutoff = datetime.now(UTC) - timedelta(minutes=2)
        result = get_entries_to_process(cutoff)

        assert result == []

    def test_multiple_entries_from_different_instances(self, actiontype):
        """Entries from multiple other instances are all processed."""
        entries = []
        entries.append(create_entry(actiontype, "192.0.2.20/32", "scram2.example.com"))
        entries.append(create_entry(actiontype, "192.0.2.21/32", "scram3.example.com"))
        cutoff = datetime.now(UTC) - timedelta(minutes=2)

        result = get_entries_to_process(cutoff)

        assert len(result) == 2
        for entry in entries:
            assert any(r.id == entry.id for r in result)

    def test_reactivated_entry_found(self, actiontype, other_instance):
        """Reactivated entries are found for reprocessing."""
        entry = create_entry(actiontype, "192.0.2.30/32", other_instance, is_active=False)
        cutoff = datetime.now(UTC)
        entry.is_active = True
        entry.save()

        result = get_entries_to_process(cutoff)

        assert len(result) == 1
        assert result[0].is_active is True

    def test_future_expiration_entry_active(self, actiontype, other_instance):
        """Entries with future expiration are processed as active."""
        _ = create_entry(
            actiontype, "192.0.2.40/32", other_instance, expiration=datetime.now(UTC) + timedelta(hours=1)
        )
        cutoff = datetime.now(UTC) - timedelta(minutes=2)

        result = get_entries_to_process(cutoff)

        assert len(result) == 1
        assert result[0].is_active is True

    def test_expired_entry_found_as_inactive(self, actiontype, other_instance):
        """Expired entries are found but marked inactive after process_updates expires them."""
        entry = create_entry(
            actiontype, "192.0.2.50/32", other_instance, expiration=datetime.now(UTC) - timedelta(hours=1)
        )
        cutoff = datetime.now(UTC) - timedelta(minutes=2)

        result = get_entries_to_process(cutoff)

        assert len(result) == 1
        assert result[0].id == entry.id


class TestCheckForOrphanedHistory:
    """Tests for check_for_orphaned_history()."""

    def test_logs_warning_for_orphaned_entries(self, caplog, actiontype, other_instance):
        """Make sure we log a warning when history exists but Entry was deleted from underneath us."""
        entry = create_entry(actiontype, "10.1.0.1/32", other_instance)
        orphaned_id = entry.id

        # Hard delete (bypass model's soft delete)
        Entry.objects.filter(id=orphaned_id).delete()
        check_for_orphaned_history({orphaned_id}, [])

        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "WARNING"
        assert str(orphaned_id) in caplog.records[0].message

    def test_no_warning_when_entry_exists(self, caplog, actiontype, other_instance):
        """No warning when all entries in the set exist."""
        entry = create_entry(actiontype, "10.1.0.2/32", other_instance)

        check_for_orphaned_history({entry.id}, [entry])

        assert len(caplog.records) == 0

    def test_accounts_for_local_entries(self, caplog, actiontype, current_instance):
        """Local entries excluded from processing are not flagged as orphans."""
        local_entry = create_entry(actiontype, "10.1.0.3/32", current_instance)

        # Entry exists but was excluded from entries_to_process because it's local
        check_for_orphaned_history({local_entry.id}, [])

        assert len(caplog.records) == 0
