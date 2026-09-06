"""Test catalogue persistence stores."""

import sqlite3

import pytest

from moniker.domain import Source
from moniker.stores import SourceStore


def seed_sources(
    connection: sqlite3.Connection,
) -> None:
    """Insert representative sources directly into the database."""
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
                "Doctor Who",
                "A British science-fiction television series.",
                "television",
            ),
            (
                "Greek mythology",
                "The mythology of ancient Greece.",
                "mythology",
            ),
            (
                "Portal 2",
                "A puzzle-platform video game.",
                "game",
            ),
            (
                "Portal 2",
                "A novelisation that definitely exists for testing purposes.",
                "book",
            ),
        ),
    )

    connection.commit()


@pytest.mark.parametrize(
    ("title_input", "type_input", "expected"),
    [
        pytest.param(
            "Doctor Who",
            "television",
            Source(
                title="Doctor Who",
                description="A British science-fiction television series.",
                type="television",
            ),
            id="returns_existing_source",
        ),
        pytest.param(
            "Doctor Who",
            "book",
            None,
            id="returns_none_when_source_missing",
        ),
        pytest.param(
            "Portal 2",
            "game",
            Source(
                title="Portal 2",
                description="A puzzle-platform video game.",
                type="game",
            ),
            id="distinguishes_composite_key_game",
        ),
        pytest.param(
            "Portal 2",
            "book",
            Source(
                title="Portal 2",
                description="A novelisation that definitely exists "
                "for testing purposes.",
                type="book",
            ),
            id="distinguishes_composite_key_book",
        ),
    ],
)
def test_source_store_gets_source(
    database: sqlite3.Connection,
    title_input: str,
    type_input: str,
    expected: Source | None,
) -> None:
    """R-BICEP: Right."""
    seed_sources(database)
    store = SourceStore(database)

    source = store.get(
        title_input,
        type_input,
    )

    assert source == expected


@pytest.mark.parametrize(
    ("title_input", "type_input"),
    [
        pytest.param(
            "",
            "book",
            id="empty_title",
        ),
        pytest.param(
            "   ",
            "book",
            id="whitespace_title",
        ),
        pytest.param(
            "Doctor Who",
            "",
            id="empty_type",
        ),
        pytest.param(
            "Doctor Who",
            "   ",
            id="whitespace_type",
        ),
    ],
)
def test_source_store_get_rejects_empty_identity(
    database: sqlite3.Connection,
    title_input: str,
    type_input: str,
) -> None:
    """R-BICEP: Error."""
    store = SourceStore(database)

    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        store.get(
            title_input,
            type_input,
        )


@pytest.mark.parametrize(
    ("title_input", "type_input", "expected"),
    [
        pytest.param(
            None,
            None,
            (
                ("Doctor Who", "television"),
                ("Greek mythology", "mythology"),
                ("Portal 2", "book"),
                ("Portal 2", "game"),
            ),
            id="all_results_in_order",
        ),
        pytest.param(
            "Portal 2",
            None,
            (
                ("Portal 2", "book"),
                ("Portal 2", "game"),
            ),
            id="filters_by_title",
        ),
        pytest.param(
            None,
            "mythology",
            (("Greek mythology", "mythology"),),
            id="filters_by_type",
        ),
        pytest.param(None, "film", (), id="filters_return_empty_when_no_match"),
        pytest.param(
            "Portal 2",
            "game",
            (("Portal 2", "game"),),
            id="filters_by_title_and_type",
        ),
    ],
)
def test_source_store_lists_sources(
    database: sqlite3.Connection,
    title_input: str | None,
    type_input: str | None,
    expected: tuple[Source, ...],
) -> None:
    """R-BICEP: Right."""
    seed_sources(database)
    store = SourceStore(database)

    sources = store.list(title=title_input, source_type=type_input)

    assert tuple((source.title, source.type) for source in sources) == expected


@pytest.mark.parametrize(
    ("title_input", "type_input"),
    [
        pytest.param(
            "",
            None,
            id="empty_title",
        ),
        pytest.param(
            "   ",
            None,
            id="whitespace_title",
        ),
        pytest.param(
            None,
            "",
            id="empty_type",
        ),
        pytest.param(
            None,
            "   ",
            id="whitespace_type",
        ),
        pytest.param(
            "",
            "",
            id="both_empty",
        ),
    ],
)
def test_source_store_list_rejects_empty_filters(
    database: sqlite3.Connection,
    title_input: str | None,
    type_input: str | None,
) -> None:
    """R-BICEP: Error."""
    store = SourceStore(database)

    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        store.list(
            title=title_input,
            source_type=type_input,
        )


@pytest.mark.parametrize(
    "source",
    [
        pytest.param(
            Source(
                title="His Dark Materials",
                description="A fantasy trilogy by Philip Pullman.",
                type="book",
            ),
            id="source_with_description",
        ),
        pytest.param(
            Source(
                title="Earthsea",
                description=None,
                type="book",
            ),
            id="source_without_description",
        ),
    ],
)
def test_source_store_creates_source(
    database: sqlite3.Connection,
    source: Source,
) -> None:
    """R-BICEP: Right."""
    store = SourceStore(database)

    result = store.create(source)

    row = database.execute(
        """
        SELECT
            title,
            description,
            type
        FROM sources
        WHERE title = ?
          AND type = ?
        """,
        (
            source.title,
            source.type,
        ),
    ).fetchone()

    assert result == source
    assert row is not None
    assert row["title"] == source.title
    assert row["description"] == source.description
    assert row["type"] == source.type


@pytest.mark.parametrize(
    "source",
    [
        pytest.param(
            Source(
                title="Doctor Who",
                description="Different description.",
                type="television",
            ),
            id="duplicate_composite_identity",
        ),
        pytest.param(
            Source(
                title="Portal 2",
                description="Another game description.",
                type="game",
            ),
            id="duplicate_title_and_type",
        ),
    ],
)
def test_source_store_rejects_duplicate_source(
    database: sqlite3.Connection,
    source: Source,
) -> None:
    """R-BICEP: Error."""
    seed_sources(database)
    store = SourceStore(database)

    with pytest.raises(sqlite3.IntegrityError):
        store.create(source)
