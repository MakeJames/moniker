"""Test the ability for Moniker to upgrade its database."""

import sqlite3
from pathlib import Path

from moniker.migrate import current_version, discover_migrations, migrate


def test_migrations_create_latest_schema(
    tmp_path: Path,
) -> None:
    """R-BICEP: Right."""
    database = tmp_path / "moniker.db"

    number_of_migrations = len(discover_migrations())

    with sqlite3.connect(database) as connection:
        version = migrate(connection)

        assert version == number_of_migrations
        assert current_version(connection) == number_of_migrations


def test_migrations_can_be_run_twice(
    tmp_path: Path,
) -> None:
    """R-BICEP: Boundary."""
    database = tmp_path / "moniker.db"

    with sqlite3.connect(database) as connection:
        first = migrate(connection)
        second = migrate(connection)

        assert first == second
