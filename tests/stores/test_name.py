"""Test catalogue persistence stores."""

import sqlite3
from typing import TypedDict

import pytest

from moniker.domain import Name, NameState, Source
from moniker.stores import NameStore


class ListNameFilters(TypedDict, total=False):
    """Typed dict for name filters."""

    source_title: str | None
    source_type: str | None
    enabled: bool | None
    state: NameState | None


class ListTagFilters(TypedDict, total=False):
    """Typed dict for tag filters."""

    name: str | None
    source_title: str | None
    source_type: str | None
    enabled: bool | None
    state: NameState | None


class TestNameStore:
    """Test the methods of the NameStore."""

    def name_values(self, names: tuple[Name, ...]) -> tuple[str, ...]:
        """Return just the values from a collection of names."""
        return tuple(name.value for name in names)

    @pytest.mark.parametrize(
        ("filters", "expected"),
        [
            pytest.param(
                {},
                (
                    "apple",
                    "apricot",
                    "beetroot",
                    "blackberry",
                    "blueberry",
                    "broccoli",
                    "cabbage",
                    "carrot",
                    "cherry",
                    "courgette",
                    "cucumber",
                    "garlic",
                    "kale",
                    "lemon",
                    "onion",
                    "parsnip",
                    "peach",
                    "pear",
                    "pepper",
                    "plum",
                    "spinach",
                    "strawberry",
                    "tomato",
                ),
                id="enabled_names",
            ),
            pytest.param(
                {"enabled": False},
                (
                    "lime",
                    "turnip",
                ),
                id="disabled_names",
            ),
            pytest.param(
                {"state": NameState.ALLOCATED},
                (
                    "apple",
                    "carrot",
                    "tomato",
                ),
                id="allocated_names",
            ),
            pytest.param(
                {"state": NameState.RESERVED},
                (
                    "blueberry",
                    "kale",
                    "lemon",
                ),
                id="reserved_names",
            ),
            pytest.param(
                {"tags": ("fruit", "orchard")},
                (
                    "apple",
                    "apricot",
                    "cherry",
                    "peach",
                    "pear",
                    "plum",
                ),
                id="multiple_tags_use_and_semantics",
            ),
            pytest.param(
                {"source_title": "Orchard"},
                (
                    "apple",
                    "apricot",
                    "cherry",
                    "peach",
                    "pear",
                    "plum",
                ),
                id="source_title",
            ),
            pytest.param(
                {"source_type": "storage-area"},
                (
                    "apple",
                    "beetroot",
                    "carrot",
                    "garlic",
                    "onion",
                    "parsnip",
                    "pear",
                ),
                id="source_type",
            ),
            pytest.param(
                {
                    "source_title": "Root Cellar",
                    "state": NameState.AVAILABLE,
                },
                (
                    "beetroot",
                    "garlic",
                    "onion",
                    "parsnip",
                    "pear",
                ),
                id="combined_filters",
            ),
            pytest.param(
                {"tags": ("does-not-exist",)},
                (),
                id="no_matches",
            ),
        ],
    )
    def test_name_store_lists_names(
        self,
        seeded_database: sqlite3.Connection,
        filters: ListNameFilters,
        expected: tuple[str, ...],
    ) -> None:
        """R-BICEP: Right and Boundary."""
        store = NameStore(seeded_database)

        names = store.list(**filters)

        assert self.name_values(names) == expected

    @pytest.mark.parametrize(
        "filters",
        [
            pytest.param(
                {"tags": ("",)},
                id="empty_tag",
            ),
            pytest.param(
                {"tags": ("   ",)},
                id="whitespace_tag",
            ),
            pytest.param(
                {"source_title": ""},
                id="empty_source_title",
            ),
            pytest.param(
                {"source_title": "   "},
                id="whitespace_source_title",
            ),
            pytest.param(
                {"source_type": ""},
                id="empty_source_type",
            ),
            pytest.param(
                {"source_type": "   "},
                id="whitespace_source_type",
            ),
        ],
    )
    def test_name_store_list_rejects_empty_filters(
        self,
        seeded_database: sqlite3.Connection,
        filters: ListNameFilters,
    ) -> None:
        """R-BICEP: Error."""
        store = NameStore(seeded_database)

        with pytest.raises(
            ValueError,
            match="must not be empty",
        ):
            store.list(**filters)

    def test_name_store_gets_complete_name(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Right."""
        store = NameStore(seeded_database)

        name = store.get("apple")

        assert name is not None
        assert name.value == "apple"
        assert name.description == "Test fruit entry for apple."
        assert name.enabled is True
        assert name.state == NameState.ALLOCATED
        assert name.tags == (
            "fruit",
            "orchard",
            "storage",
            "sweet",
        )
        assert tuple(source.title for source in name.sources) == (
            "Orchard",
            "Root Cellar",
        )

    @pytest.mark.parametrize(
        "value",
        [
            "cherry",
            "cucumber",
        ],
    )
    def test_name_store_get_uses_latest_event(
        self,
        seeded_database: sqlite3.Connection,
        value: str,
    ) -> None:
        """R-BICEP: Boundary."""
        store = NameStore(seeded_database)

        name = store.get(value)

        assert name is not None
        assert name.state == NameState.AVAILABLE

    def test_name_store_get_returns_none_when_missing(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Boundary."""
        store = NameStore(seeded_database)

        assert store.get("dragonfruit") is None

    @pytest.mark.parametrize(
        "value",
        [
            "",
            "   ",
        ],
    )
    def test_name_store_get_rejects_empty_name(
        self,
        seeded_database: sqlite3.Connection,
        value: str,
    ) -> None:
        """R-BICEP: Error."""
        store = NameStore(seeded_database)

        with pytest.raises(
            ValueError,
            match="name must not be empty",
        ):
            store.get(value)

    @pytest.mark.parametrize(
        ("query", "expected"),
        [
            pytest.param(
                "berry",
                (
                    "blackberry",
                    "blueberry",
                    "strawberry",
                ),
                id="partial_match",
            ),
            pytest.param(
                "PEA",
                (
                    "peach",
                    "pear",
                ),
                id="case_insensitive",
            ),
            pytest.param(
                "lime",
                ("lime",),
                id="includes_disabled_names",
            ),
            pytest.param(
                "dragonfruit",
                (),
                id="no_matches",
            ),
        ],
    )
    def test_name_store_finds_names(
        self,
        seeded_database: sqlite3.Connection,
        query: str,
        expected: tuple[str, ...],
    ) -> None:
        """R-BICEP: Right and Boundary."""
        store = NameStore(seeded_database)

        names = store.find(query)

        assert self.name_values(names) == expected

    def _seed_search_name(
        self,
        connection: sqlite3.Connection,
        value: str,
    ) -> None:
        connection.execute(
            """
            insert into names (
                name,
                description,
                enabled
            )
            values (?, null, 1)
            """,
            (value,),
        )

        connection.execute(
            """
            insert into name_events (
                name,
                assigned_to,
                event,
                state,
                occurred_at
            )
            values (
                ?,
                null,
                'created',
                'available',
                '2026-09-07T00:00:00Z'
            )
            """,
            (value,),
        )

    @pytest.mark.parametrize(
        ("literal", "matching", "decoy"),
        [
            (
                "%",
                "percent%fruit",
                "percentafruit",
            ),
            (
                "_",
                "under_score",
                "underXscore",
            ),
        ],
    )
    def test_name_store_find_treats_wildcards_as_literals(
        self,
        seeded_database: sqlite3.Connection,
        literal: str,
        matching: str,
        decoy: str,
    ) -> None:
        """R-BICEP: Boundary."""
        self._seed_search_name(
            seeded_database,
            matching,
        )
        self._seed_search_name(
            seeded_database,
            decoy,
        )

        store = NameStore(seeded_database)

        names = store.find(literal)

        assert self.name_values(names) == (matching,)

    @pytest.mark.parametrize(
        "query",
        [
            "",
            "   ",
        ],
    )
    def test_name_store_find_rejects_empty_query(
        self,
        seeded_database: sqlite3.Connection,
        query: str,
    ) -> None:
        """R-BICEP: Error."""
        store = NameStore(seeded_database)

        with pytest.raises(
            ValueError,
            match="query must not be empty",
        ):
            store.find(query)

    @pytest.mark.parametrize(
        ("filters", "expected"),
        [
            pytest.param(
                {
                    "name": "apple",
                    "state": None,
                },
                (
                    "fruit",
                    "orchard",
                    "storage",
                    "sweet",
                ),
                id="name",
            ),
            pytest.param(
                {
                    "source_title": "Root Cellar",
                    "state": None,
                },
                (
                    "allium",
                    "fruit",
                    "orchard",
                    "root",
                    "storage",
                    "sweet",
                    "vegetable",
                ),
                id="source",
            ),
            pytest.param(
                {
                    "state": NameState.ALLOCATED,
                },
                (
                    "fruit",
                    "greenhouse",
                    "orchard",
                    "root",
                    "storage",
                    "sweet",
                    "vegetable",
                ),
                id="current_state",
            ),
            pytest.param(
                {
                    "name": "lime",
                    "state": None,
                },
                (),
                id="disabled_excluded_by_default",
            ),
            pytest.param(
                {
                    "name": "lime",
                    "enabled": False,
                    "state": None,
                },
                (
                    "citrus",
                    "fruit",
                    "greenhouse",
                ),
                id="disabled_explicitly_selected",
            ),
        ],
    )
    def test_name_store_lists_tags(
        self,
        seeded_database: sqlite3.Connection,
        filters: ListTagFilters,
        expected: tuple[str, ...],
    ) -> None:
        """R-BICEP: Right and Boundary."""
        store = NameStore(seeded_database)

        tags = store.list_tags(**filters)

        assert tags == expected

    def test_name_store_picks_from_filtered_candidates(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Right."""
        store = NameStore(seeded_database)

        name = store.pick(
            tags=(
                "brassica",
                "leafy",
            ),
        )

        assert name is not None
        assert name.value == "cabbage"
        assert name.state == NameState.AVAILABLE

    def test_name_store_pick_returns_none_when_no_name_is_available(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Boundary."""
        store = NameStore(seeded_database)

        name = store.pick(
            tags=("citrus",),
        )

        assert name is None

    def test_name_store_creates_name_metadata(
        self,
        database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Right."""
        store = NameStore(database)

        name = Name(
            value="dragonfruit",
            description="A test fruit.",
            enabled=True,
        )

        result = store.create(name)

        row = database.execute(
            """
            select
                name,
                description,
                enabled
            from names
            where name = ?
            """,
            ("dragonfruit",),
        ).fetchone()

        assert result == name
        assert row is not None
        assert row["description"] == "A test fruit."
        assert row["enabled"] == 1

    def test_name_store_create_does_not_create_lifecycle_event(
        self,
        database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Boundary."""
        store = NameStore(database)

        store.create(
            Name(
                value="dragonfruit",
            )
        )

        events = database.execute(
            """
            select *
            from name_events
            where name = ?
            """,
            ("dragonfruit",),
        ).fetchall()

        assert events == []

    def test_name_store_rejects_duplicate_name(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Error."""
        store = NameStore(seeded_database)

        with pytest.raises(sqlite3.IntegrityError):
            store.create(
                Name(
                    value="apple",
                )
            )

    def test_name_store_adds_tags(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Right."""
        store = NameStore(seeded_database)
        apple = store.get("apple")

        assert apple is not None

        updated = store.add_tags(
            apple,
            (
                "seasonal",
                "local",
            ),
        )

        assert updated.tags == (
            "fruit",
            "local",
            "orchard",
            "seasonal",
            "storage",
            "sweet",
        )

    def test_name_store_add_tags_ignores_existing_and_duplicate_tags(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Boundary."""
        store = NameStore(seeded_database)
        apple = store.get("apple")

        assert apple is not None

        updated = store.add_tags(
            apple,
            (
                "fruit",
                "seasonal",
                "seasonal",
            ),
        )

        assert updated.tags.count("fruit") == 1
        assert updated.tags.count("seasonal") == 1

    @pytest.mark.parametrize(
        "tag",
        [
            "",
            "   ",
        ],
    )
    def test_name_store_add_tags_rejects_empty_tag(
        self,
        seeded_database: sqlite3.Connection,
        tag: str,
    ) -> None:
        """R-BICEP: Error."""
        store = NameStore(seeded_database)
        apple = store.get("apple")

        assert apple is not None

        with pytest.raises(
            ValueError,
            match="tag must not be empty",
        ):
            store.add_tags(
                apple,
                (tag,),
            )

    def test_name_store_adds_source(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Right."""
        store = NameStore(seeded_database)
        blackberry = store.get("blackberry")

        assert blackberry is not None

        updated = store.add_source(
            blackberry,
            Source(
                title="Orchard",
                type="growing-area",
            ),
        )

        assert tuple(source.title for source in updated.sources) == (
            "Berry Patch",
            "Orchard",
        )

    def test_name_store_rejects_duplicate_source_relationship(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Error."""
        store = NameStore(seeded_database)
        blackberry = store.get("blackberry")

        assert blackberry is not None

        with pytest.raises(sqlite3.IntegrityError):
            store.add_source(
                blackberry,
                Source(
                    title="Berry Patch",
                    type="growing-area",
                ),
            )

    def test_name_store_rejects_unknown_source(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Error."""
        store = NameStore(seeded_database)
        apple = store.get("apple")

        assert apple is not None

        with pytest.raises(sqlite3.IntegrityError):
            store.add_source(
                apple,
                Source(
                    title="Moon Base",
                    type="growing-area",
                ),
            )

    def test_name_store_can_list_all_names(
        self,
        seeded_database: sqlite3.Connection,
        catalogue_item_count: int,
    ) -> None:
        """R-BICEP: Boundary."""
        store = NameStore(seeded_database)

        names = store.list(enabled=None, state=None)
        values = self.name_values(names)

        assert len(values) == catalogue_item_count
        assert "apple" in values
        assert "lime" in values
        assert "turnip" in values
