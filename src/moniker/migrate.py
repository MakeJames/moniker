"""Version and upgrade the database."""

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from moniker.database import connect, database_path


MIGRATIONS_PATH = Path(__file__).with_name("migrations")

MIGRATION_PATTERN = re.compile(
    r"^(?P<version>\d{4})_(?P<name>[a-z0-9_]+)\.sql$"
)


class UnrecognisedMigrationFileError(Exception):
    """Error when file names do not match the migration pattern."""

    ...


@dataclass(frozen=True)
class Migration:
    """Migration data object."""

    version: int
    name: str
    path: Path


def current_version(connection: sqlite3.Connection) -> int:
    """Establish current version of the database."""
    row = connection.execute("PRAGMA user_version").fetchone()

    if row is None:
        return 0

    return int(row[0])


def discover_migrations(
    path: Path = MIGRATIONS_PATH,
) -> tuple[Migration, ...]:
    """Find schema migrations."""
    migrations = []

    for migration_path in path.glob("*.sql"):
        match = MIGRATION_PATTERN.match(migration_path.name)

        if match is None:
            raise UnrecognisedMigrationFileError(
                f"File name {migration_path} is not recognised. "
                "Ensure that the file name is correctly formatted."
            )

        migrations.append(
            Migration(
                version=int(match.group("version")),
                name=match.group("name"),
                path=migration_path,
            )
        )

    return tuple(
        sorted(
            migrations,
            key=lambda migration: migration.version,
        )
    )


def validate_migrations(
    migrations: tuple[Migration, ...],
) -> None:
    """Assert migration order."""
    expected = 1

    for migration in migrations:
        if migration.version != expected:
            raise RuntimeError(
                "Expected migration "
                f"{expected:04d}, "
                f"found {migration.version:04d}"
            )

        expected += 1


def apply_migration(
    connection: sqlite3.Connection,
    migration: Migration,
) -> None:
    """Try to apply the migration."""
    sql = migration.path.read_text(encoding="utf-8")

    try:
        connection.executescript(sql)
    except sqlite3.Error:
        if connection.in_transaction:
            connection.rollback()

        raise

    version = current_version(connection)

    if version != migration.version:
        raise RuntimeError(
            f"Migration {migration.path.name} did not set "
            f"PRAGMA user_version = {migration.version}"
        )


def migrate(
    connection: sqlite3.Connection,
) -> int:
    """Orchestrate the migration path."""
    migrations = discover_migrations()
    validate_migrations(migrations)

    version = current_version(connection)

    if migrations and version > migrations[-1].version:
        raise RuntimeError(
            f"Database schema version {version} is newer than "
            f"this application supports "
            f"({migrations[-1].version})"
        )

    for migration in migrations:
        if migration.version <= version:
            continue

        print(f"Applying {migration.version:04d}: {migration.name}")

        apply_migration(connection, migration)
        version = migration.version

    return version


def main() -> None:
    """Migrate database."""
    path = database_path()

    with connect(path) as connection:
        version = migrate(connection)

    print(f"Database: {path}")
    print(f"Schema version: {version}")


if __name__ == "__main__":
    main()
