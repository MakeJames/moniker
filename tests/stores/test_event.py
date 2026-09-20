"""Test the methods of the event module."""

import sqlite3
from datetime import UTC, datetime

import pytest

from moniker.domain import NameEvent, NameEventType, NameState
from moniker.stores import NameEventStore


def test_name_event_store_gets_latest_event(
    seeded_database: sqlite3.Connection,
) -> None:
    """R-BICEP: Right."""
    store = NameEventStore(seeded_database)

    event = store.latest("apple")

    assert event is not None
    assert event.name == "apple"
    assert event.event == NameEventType.ALLOCATED
    assert event.state == NameState.ALLOCATED
    assert event.assigned_to == "device-01"


def test_name_event_store_latest_uses_most_recent_event(
    seeded_database: sqlite3.Connection,
) -> None:
    """R-BICEP: Boundary."""
    store = NameEventStore(seeded_database)

    event = store.latest("cherry")

    assert event is not None
    assert event.event == NameEventType.RELEASED
    assert event.state == NameState.AVAILABLE


def test_name_event_store_latest_returns_none_when_missing(
    seeded_database: sqlite3.Connection,
) -> None:
    """R-BICEP: Boundary."""
    store = NameEventStore(seeded_database)

    assert store.latest("dragonfruit") is None


def test_name_event_store_returns_history_in_order(
    seeded_database: sqlite3.Connection,
) -> None:
    """R-BICEP: Right."""
    store = NameEventStore(seeded_database)

    events = store.history("cherry")

    assert tuple(event.event for event in events) == (
        NameEventType.CREATED,
        NameEventType.ALLOCATED,
        NameEventType.RELEASED,
    )


def test_name_event_store_returns_empty_history_when_missing(
    seeded_database: sqlite3.Connection,
) -> None:
    """R-BICEP: Boundary."""
    store = NameEventStore(seeded_database)

    assert store.history("dragonfruit") == ()


def test_name_event_store_appends_event(
    database: sqlite3.Connection,
) -> None:
    """R-BICEP: Right."""
    database.execute(
        """
        insert into names (
            name,
            description,
            enabled
        )
        values (?, null, 1)
        """,
        ("dragonfruit",),
    )

    store = NameEventStore(database)

    event = NameEvent(
        name="dragonfruit",
        event=NameEventType.CREATED,
        state=NameState.AVAILABLE,
        occurred_at=datetime(
            2026,
            9,
            20,
            12,
            0,
            tzinfo=UTC,
        ),
    )

    result = store.append(event)

    assert result == event

    persisted = store.latest("dragonfruit")

    assert persisted == event


def test_name_event_store_rejects_unknown_name(
    database: sqlite3.Connection,
) -> None:
    """R-BICEP: Error."""
    store = NameEventStore(database)

    event = NameEvent(
        name="dragonfruit",
        event=NameEventType.CREATED,
        state=NameState.AVAILABLE,
        occurred_at=datetime.now(UTC),
    )

    with pytest.raises(sqlite3.IntegrityError):
        store.append(event)


def test_name_event_store_rejects_invalid_event_state(
    seeded_database: sqlite3.Connection,
) -> None:
    """R-BICEP: Error."""
    store = NameEventStore(seeded_database)

    event = NameEvent(
        name="apple",
        event=NameEventType.ALLOCATED,
        state=NameState.AVAILABLE,
        occurred_at=datetime(
            2026,
            9,
            21,
            tzinfo=UTC,
        ),
    )

    with pytest.raises(sqlite3.IntegrityError):
        store.append(event)
