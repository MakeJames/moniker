"""Test fixtures and settings."""

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest

from moniker.database import connect
from moniker.migrate import migrate
from moniker.utils import utc_now, to_utc_string


@pytest.fixture
def database(
    tmp_path: Path,
) -> Iterator[sqlite3.Connection]:
    """Database connection in a tmp directory."""
    path = tmp_path / "moniker.db"

    with connect(path) as connection:
        migrate(connection)

        yield connection


@pytest.fixture
def seeded_database(
    database: sqlite3.Connection,
) -> sqlite3.Connection:
    """Add data to test database."""
    created_at = to_utc_string(utc_now())

    database.executemany(
        """
        INSERT INTO names (
            name,
            source,
            description,
            enabled,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            (
                "calcifer",
                "Howl's Moving Castle",
                "A fire demon who powers Howl's castle.",
                0,
                created_at,
            ),
            (
                "iorek",
                "His Dark Materials",
                "Armoured, dependable and formidable.",
                1,
                created_at,
            ),
            (
                "tardis",
                "Doctor Who",
                "Bigger on the inside.",
                0,
                created_at,
            ),
            (
                "marvin",
                "The Hitchhiker's Guide to the Galaxy",
                "Exceptionally capable and rarely impressed.",
                0,
                created_at,
            ),
        ),
    )

    database.executemany(
        """
        INSERT INTO tags (
            name,
            tag
        )
        VALUES (?, ?)
        """,
        (
            ("calcifer", "compute"),
            ("calcifer", "fantasy"),
            ("calcifer", "fire"),
            ("iorek", "server"),
            ("iorek", "storage"),
            ("iorek", "fantasy"),
            ("tardis", "storage"),
            ("tardis", "science-fiction"),
            ("marvin", "compute"),
            ("marvin", "automation"),
            ("marvin", "science-fiction"),
        ),
    )

    database.commit()

    return database
