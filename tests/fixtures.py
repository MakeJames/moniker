"""Reusable test data and database seed helpers."""

import sqlite3

from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from moniker.domain import NameEventType, NameState
from moniker.utils import to_utc_string


FIXTURE_PATH = Path(__file__).parent / "catalogue.yaml"

EVENT_STATES = {
    NameEventType.CREATED: NameState.AVAILABLE,
    NameEventType.ALLOCATED: NameState.ALLOCATED,
    NameEventType.RESERVED: NameState.RESERVED,
    NameEventType.RELEASED: NameState.AVAILABLE,
}


def _timestamp(value: str | datetime) -> str:
    """Return a fixture timestamp in Moniker's UTC storage format."""
    if isinstance(value, datetime):
        return to_utc_string(value)

    return value


def _load_catalogue_fixture(
    path: Path = FIXTURE_PATH,
) -> dict[str, Any]:
    """Load the representative catalogue fixture from YAML."""
    with path.open(encoding="utf-8") as fixture:
        data = yaml.safe_load(fixture)

    if not isinstance(data, dict):
        raise ValueError("Catalogue fixture must contain a mapping")
    return data


def _seed_sources(
    connection: sqlite3.Connection,
    sources: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Seed sources and return them indexed by title."""
    connection.executemany(
        """
        INSERT INTO sources (
            title,
            description,
            type
        )
        VALUES (?, ?, ?)
        """,
        (
            (
                source["title"],
                source.get("description"),
                source["type"],
            )
            for source in sources
        ),
    )

    return {source["title"]: source for source in sources}


def _seed_name(
    connection: sqlite3.Connection,
    item: dict[str, Any],
    *,
    default_enabled: bool,
) -> None:
    """Seed the persisted metadata for a catalogue name."""
    connection.execute(
        """
        INSERT INTO names (
            name,
            description,
            enabled
        )
        VALUES (?, ?, ?)
        """,
        (
            item["value"],
            item.get("description"),
            int(
                item.get(
                    "enabled",
                    default_enabled,
                )
            ),
        ),
    )


def _seed_tags(
    connection: sqlite3.Connection,
    item: dict[str, Any],
) -> None:
    """Seed tags associated with a catalogue name."""
    connection.executemany(
        """
        INSERT INTO tags (
            name,
            tag
        )
        VALUES (?, ?)
        """,
        (
            (
                item["value"],
                tag,
            )
            for tag in item.get("tags", ())
        ),
    )


def _seed_name_sources(
    connection: sqlite3.Connection,
    item: dict[str, Any],
    sources_by_title: dict[str, dict[str, Any]],
) -> None:
    """Seed source relationships for a catalogue name."""
    for source_title in item.get(
        "sources",
        (),
    ):
        if source_title not in sources_by_title:
            raise ValueError(
                f"Unknown source {source_title!r} for name {item['value']!r}"
            )

        source = sources_by_title[source_title]

        connection.execute(
            """
            INSERT INTO name_sources (
                name,
                source_title,
                source_type
            )
            VALUES (?, ?, ?)
            """,
            (
                item["value"],
                source["title"],
                source["type"],
            ),
        )


def _seed_events(
    connection: sqlite3.Connection,
    item: dict[str, Any],
    *,
    created_at: str | datetime,
) -> None:
    """Seed creation and lifecycle events for a catalogue name."""
    connection.execute(
        """
        INSERT INTO name_events (
            name,
            assigned_to,
            event,
            state,
            occurred_at
        )
        VALUES (?, NULL, ?, ?, ?)
        """,
        (
            item["value"],
            NameEventType.CREATED.value,
            NameState.AVAILABLE.value,
            _timestamp(created_at),
        ),
    )

    for event in item.get("events", ()):
        event_type = NameEventType(event["event"])

        connection.execute(
            """
            INSERT INTO name_events (
                name,
                assigned_to,
                event,
                state,
                occurred_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                item["value"],
                event.get("assigned_to"),
                event_type.value,
                EVENT_STATES[event_type].value,
                _timestamp(event["at"]),
            ),
        )


def seed_catalogue(
    connection: sqlite3.Connection,
    path: Path = FIXTURE_PATH,
) -> None:
    """Populate a database with representative catalogue data."""
    fixture = _load_catalogue_fixture(path)

    defaults = fixture["defaults"]
    sources = fixture.get("sources", ())
    names = fixture.get("names", ())

    sources_by_title = _seed_sources(
        connection,
        sources,
    )

    for item in names:
        _seed_name(
            connection,
            item,
            default_enabled=defaults["enabled"],
        )

        _seed_tags(
            connection,
            item,
        )

        _seed_name_sources(
            connection,
            item,
            sources_by_title,
        )

        _seed_events(
            connection,
            item,
            created_at=defaults["created_at"],
        )

    connection.commit()


def catalogue_name_count() -> int:
    """Return the number of names in the catalogue fixture."""
    catalogue = _load_catalogue_fixture()

    return len(
        catalogue.get(
            "names",
            [],
        )
    )
