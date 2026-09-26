"""Back up the Moniker SQLite database."""

import argparse
import sqlite3
from pathlib import Path

from moniker.database import database_path


def backup_database(
    destination: Path,
    source: Path | None = None,
) -> None:
    """Create a consistent SQLite backup."""
    source = source or database_path()

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with (
        sqlite3.connect(source) as source_connection,
        sqlite3.connect(destination) as destination_connection,
    ):
        source_connection.backup(destination_connection)


def main() -> None:
    """Back up the configured Moniker database."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "destination",
        type=Path,
    )

    args = parser.parse_args()

    backup_database(args.destination)


if __name__ == "__main__":
    main()
