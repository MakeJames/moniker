"""Reusable test data and database seed helpers."""

import sqlite3

from moniker.utils import to_utc_string, utc_now


NAMES = (
    (
        "calcifer",
        "A fire demon who powers Howl's castle.",
        True,
    ),
    (
        "iorek",
        "Armoured, dependable and formidable.",
        True,
    ),
    (
        "tardis",
        "Bigger on the inside.",
        True,
    ),
    (
        "marvin",
        "Exceptionally capable and rarely impressed.",
        False,
    ),
)


TAGS = (
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
)


SOURCES = (
    (
        "Howl's Moving Castle",
        "book",
        None,
    ),
    (
        "His Dark Materials",
        "book",
        None,
    ),
    (
        "Doctor Who",
        "television",
        None,
    ),
    (
        "The Hitchhiker's Guide to the Galaxy",
        "book",
        None,
    ),
)


NAME_SOURCES = (
    ("calcifer", "Howl's Moving Castle", "book"),
    ("iorek", "His Dark Materials", "book"),
    ("tardis", "Doctor Who", "television"),
    (
        "marvin",
        "The Hitchhiker's Guide to the Galaxy",
        "book",
    ),
)


def seed_catalogue(
    connection: sqlite3.Connection,
) -> None:
    """Populate a database with representative test catalogue data."""
    occurred_at = to_utc_string(utc_now())

    connection.executemany(
        """
        INSERT INTO names (
            name,
            description,
            enabled
        )
        VALUES (?, ?, ?)
        """,
        NAMES,
    )

    connection.executemany(
        """
        INSERT INTO tags (
            name,
            tag
        )
        VALUES (?, ?)
        """,
        TAGS,
    )

    connection.executemany(
        """
        INSERT INTO sources (
            title,
            type,
            description
        )
        VALUES (?, ?, ?)
        """,
        SOURCES,
    )

    connection.executemany(
        """
        INSERT INTO name_sources (
            name,
            source_title,
            source_type
        )
        VALUES (?, ?, ?)
        """,
        NAME_SOURCES,
    )

    connection.executemany(
        """
        INSERT INTO name_events (
            name,
            assigned_to,
            event,
            state,
            occurred_at
        )
        VALUES (?, NULL, 'created', 'available', ?)
        """,
        ((name, occurred_at) for name, _, _ in NAMES),
    )

    connection.commit()
