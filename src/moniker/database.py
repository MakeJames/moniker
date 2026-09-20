"""Manage connections to the database."""

import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

DEFAULT_DATABASE_PATH = Path("data/moniker.db")


def database_path() -> Path:
    """Resolve the location of the Database."""
    return Path(
        os.environ.get(
            "MONIKER_DATABASE",
            DEFAULT_DATABASE_PATH,
        )
    )


@contextmanager
def immediate_transaction(
    connection: sqlite3.Connection,
) -> Iterator[None]:
    """Run work inside an immediate SQLite transaction."""
    connection.execute("BEGIN IMMEDIATE")

    try:
        yield
    except Exception:
        connection.rollback()
        raise
    else:
        connection.commit()


def connect(path: Path | None = None) -> sqlite3.Connection:
    """Create a connection to the specified database."""
    path = path or database_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(path, check_same_thread=False)
    connection.row_factory = sqlite3.Row

    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")

    return connection
