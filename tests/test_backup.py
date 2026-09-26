"""Test the behaviours of the back-up script."""

import sqlite3
from pathlib import Path

from moniker.backup import backup_database


def test_backup_database(tmp_path: Path) -> None:
    """R-BICEP: Right."""
    source = tmp_path / "source.db"
    destination = tmp_path / "backup.db"

    with sqlite3.connect(source) as connection:
        connection.execute("create table example (value text)")
        connection.execute("insert into example values ('hello')")

    backup_database(
        destination,
        source,
    )

    with sqlite3.connect(destination) as connection:
        row = connection.execute("select value from example").fetchone()

    assert row == ("hello",)
