"""Test fixtures and settings."""

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest
from freezegun import freeze_time

from moniker.database import connect
from moniker.migrate import migrate

from tests.fixtures import seed_catalogue


@pytest.fixture
def database(
    tmp_path: Path,
) -> Iterator[sqlite3.Connection]:
    """Return a fresh migrated database."""
    path = tmp_path / "moniker.db"

    with connect(path) as connection:
        migrate(connection)

        yield connection


@freeze_time("2026-09-06T18:00:00Z")
@pytest.fixture
def seeded_database(
    database: sqlite3.Connection,
) -> sqlite3.Connection:
    """Return a database containing representative catalogue data."""
    seed_catalogue(database)

    return database
