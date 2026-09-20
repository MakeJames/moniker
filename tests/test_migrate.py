"""Test the ability for Moniker to upgrade its database."""

import sqlite3

from collections.abc import Iterator
from pathlib import Path

import pytest

from moniker.migrate import (
    Migration,
    UnrecognisedMigrationFileError,
    apply_migration,
    current_version,
    discover_migrations,
    migrate,
    validate_migrations,
)


@pytest.fixture
def migration_database(
    tmp_path: Path,
) -> Iterator[sqlite3.Connection]:
    """Return an empty database for migration tests."""
    database = tmp_path / "moniker.db"
    connection = sqlite3.connect(database)

    try:
        yield connection
    finally:
        connection.close()


def test_migrations_reject_unrecognised_filename(
    tmp_path: Path,
) -> None:
    """R-BICEP: Error."""
    migrations = tmp_path / "migrations"
    migrations.mkdir()

    migration = migrations / "initial.sql"
    migration.write_text("PRAGMA user_version = 1;", encoding="utf-8")

    with pytest.raises(UnrecognisedMigrationFileError, match="not recognised"):
        discover_migrations(migrations)


def test_failed_migration_rolls_back(
    migration_database: sqlite3.Connection,
    tmp_path: Path,
) -> None:
    """R-BICEP: Error and Boundary."""
    path = tmp_path / "0001_broken.sql"
    path.write_text(
        """
        BEGIN IMMEDIATE;

        CREATE TABLE partial_table (
            id INTEGER PRIMARY KEY
        );

        THIS IS NOT VALID SQL;

        PRAGMA user_version = 1;

        COMMIT;
        """,
        encoding="utf-8",
    )

    migration = Migration(version=1, name="broken", path=path)

    with pytest.raises(sqlite3.Error):
        apply_migration(migration_database, migration)

    assert current_version(migration_database) == 0

    table = migration_database.execute(
        """
        select name
        from sqlite_master
        where type = 'table'
          and name = 'partial_table'
        """
    ).fetchone()

    assert table is None


def test_migration_must_set_schema_version(
    migration_database: sqlite3.Connection,
    tmp_path: Path,
) -> None:
    """R-BICEP: Error."""
    path = tmp_path / "0001_missing_version.sql"
    path.write_text(
        """
        BEGIN IMMEDIATE;

        CREATE TABLE example (
            id INTEGER PRIMARY KEY
        );

        COMMIT;
        """,
        encoding="utf-8",
    )

    migration = Migration(version=1, name="missing_version", path=path)

    with pytest.raises(
        RuntimeError, match="did not set PRAGMA user_version = 1"
    ):
        apply_migration(migration_database, migration)

    assert current_version(migration_database) == 0


def test_migrate_rejects_newer_database(
    migration_database: sqlite3.Connection,
) -> None:
    """R-BICEP: Error."""
    latest = len(discover_migrations())
    unsupported = latest + 1

    migration_database.execute(f"PRAGMA user_version = {unsupported}")

    with pytest.raises(
        RuntimeError, match="newer than this application supports"
    ):
        migrate(migration_database)


def test_migrations_reject_version_gap(
    tmp_path: Path,
) -> None:
    """R-BICEP: Error."""
    first = Migration(
        version=1, name="initial", path=tmp_path / "0001_initial.sql"
    )
    third = Migration(version=3, name="third", path=tmp_path / "0003_third.sql")

    with pytest.raises(
        RuntimeError, match="Expected migration 0002, found 0003"
    ):
        validate_migrations((first, third))


def test_migrations_create_latest_schema(
    tmp_path: Path, migration_database: sqlite3.Connection
) -> None:
    """R-BICEP: Right."""
    number_of_migrations = len(discover_migrations())

    connection = migration_database

    version = migrate(connection)

    assert version == number_of_migrations
    assert current_version(connection) == number_of_migrations


def test_migrations_can_be_run_twice(
    tmp_path: Path, migration_database: sqlite3.Connection
) -> None:
    """R-BICEP: Boundary."""
    connection = migration_database

    first = migrate(connection)
    second = migrate(connection)

    assert first == second
