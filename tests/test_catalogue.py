"""Test application orchestration for the Moniker catalogue."""

import sqlite3

from datetime import UTC, datetime
from typing import TypedDict

import pytest

from freezegun import freeze_time

from moniker.catalogue import (
    Catalogue,
    InvalidNameTransitionError,
    NameAlreadyExistsError,
    NameNotFoundError,
    SourceAlreadyExistsError,
)
from moniker.domain import (
    Name,
    NameEventType,
    NameState,
    Source,
)


class ListNameFilters(TypedDict, total=False):
    """Optional filters accepted by Catalogue.list_names."""

    tags: tuple[str, ...]
    source_title: str | None
    source_type: str | None
    enabled: bool | None
    state: NameState | None


def name_values(
    names: tuple[Name, ...],
) -> tuple[str, ...]:
    """Return canonical values from a collection of names."""
    return tuple(name.value for name in names)


class TestSourceCatalogue:
    """Test source application operations."""

    def test_catalogue_lists_sources(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Right."""
        catalogue = Catalogue(seeded_database)

        sources = catalogue.list_sources(
            source_type="growing-area",
        )

        assert tuple(source.title for source in sources) == (
            "Berry Patch",
            "Greenhouse",
            "Kitchen Garden",
            "Orchard",
        )

    def test_catalogue_gets_source(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Right."""
        catalogue = Catalogue(seeded_database)

        source = catalogue.get_source(
            "Orchard",
            "growing-area",
        )

        assert source is not None
        assert source.title == "Orchard"
        assert source.type == "growing-area"

    def test_catalogue_returns_none_for_missing_source(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Boundary."""
        catalogue = Catalogue(seeded_database)

        source = catalogue.get_source(
            "Moon Base",
            "growing-area",
        )

        assert source is None

    def test_catalogue_creates_source(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Right."""
        catalogue = Catalogue(seeded_database)

        source = Source(
            title="Polytunnel",
            description="A covered growing area.",
            type="growing-area",
        )

        created = catalogue.create_source(source)

        assert created == source
        assert (
            catalogue.get_source(
                "Polytunnel",
                "growing-area",
            )
            == source
        )

    def test_catalogue_rejects_duplicate_source(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Error."""
        catalogue = Catalogue(seeded_database)

        source = Source(
            title="Orchard",
            description="Different metadata.",
            type="growing-area",
        )

        with pytest.raises(SourceAlreadyExistsError):
            catalogue.create_source(source)


class TestNameCatalogue:
    """Test name discovery and retrieval operations."""

    @pytest.mark.parametrize(
        ("filters", "expected"),
        [
            pytest.param(
                {
                    "enabled": False,
                },
                (
                    "lime",
                    "turnip",
                ),
                id="disabled_names",
            ),
            pytest.param(
                {
                    "state": NameState.ALLOCATED,
                },
                (
                    "apple",
                    "carrot",
                    "tomato",
                ),
                id="allocated_names",
            ),
            pytest.param(
                {
                    "tags": (
                        "fruit",
                        "orchard",
                    ),
                    "state": NameState.AVAILABLE,
                },
                (
                    "apricot",
                    "cherry",
                    "peach",
                    "pear",
                    "plum",
                ),
                id="combined_tag_and_state",
            ),
            pytest.param(
                {
                    "source_type": "storage-area",
                    "state": NameState.AVAILABLE,
                },
                (
                    "beetroot",
                    "garlic",
                    "onion",
                    "parsnip",
                    "pear",
                ),
                id="combined_source_and_state",
            ),
            pytest.param(
                {
                    "tags": ("not-a-tag",),
                },
                (),
                id="no_matches",
            ),
        ],
    )
    def test_catalogue_lists_names(
        self,
        seeded_database: sqlite3.Connection,
        filters: ListNameFilters,
        expected: tuple[str, ...],
    ) -> None:
        """R-BICEP: Right and Boundary."""
        catalogue = Catalogue(seeded_database)

        names = catalogue.list_names(**filters)

        assert name_values(names) == expected

    def test_catalogue_gets_name(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Right."""
        catalogue = Catalogue(seeded_database)

        name = catalogue.get_name("apple")

        assert name is not None
        assert name.value == "apple"
        assert name.enabled is True
        assert name.state == NameState.ALLOCATED
        assert name.tags == (
            "fruit",
            "orchard",
            "storage",
            "sweet",
        )

    def test_catalogue_returns_none_for_missing_name(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Boundary."""
        catalogue = Catalogue(seeded_database)

        assert catalogue.get_name("dragonfruit") is None

    def test_catalogue_finds_names(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Right."""
        catalogue = Catalogue(seeded_database)

        names = catalogue.find_names("berry")

        assert name_values(names) == (
            "blackberry",
            "blueberry",
            "strawberry",
        )

    def test_catalogue_lists_tags_for_name(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Right."""
        catalogue = Catalogue(seeded_database)

        tags = catalogue.list_tags(
            name="apple",
        )

        assert tags == (
            "fruit",
            "orchard",
            "storage",
            "sweet",
        )

    def test_catalogue_lists_tags_for_filtered_names(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Boundary."""
        catalogue = Catalogue(seeded_database)

        tags = catalogue.list_tags(
            source_title="Root Cellar",
            state=NameState.AVAILABLE,
        )

        assert tags == (
            "allium",
            "fruit",
            "orchard",
            "root",
            "storage",
            "sweet",
            "vegetable",
        )


class TestSuggestionCatalogue:
    """Test name suggestion orchestration."""

    def test_catalogue_suggests_available_name(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Right."""
        catalogue = Catalogue(seeded_database)

        name = catalogue.suggest_name(
            tags=(
                "brassica",
                "leafy",
            ),
        )

        assert name is not None
        assert name.value == "cabbage"
        assert name.enabled is True
        assert name.state == NameState.AVAILABLE

    def test_catalogue_suggestion_combines_filters(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Right."""
        catalogue = Catalogue(seeded_database)

        name = catalogue.suggest_name(
            tags=("storage",),
            source_title="Orchard",
        )

        assert name is not None
        assert name.value == "pear"

    def test_catalogue_returns_none_without_candidate(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Boundary."""
        catalogue = Catalogue(seeded_database)

        name = catalogue.suggest_name(
            tags=("citrus",),
        )

        assert name is None

    def test_catalogue_does_not_suggest_disabled_name(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Boundary."""
        catalogue = Catalogue(seeded_database)

        name = catalogue.suggest_name(
            tags=(
                "fruit",
                "citrus",
                "greenhouse",
            ),
        )

        assert name is None


class TestCreateNameCatalogue:
    """Test complete name creation orchestration."""

    @freeze_time("2026-09-20T16:00:00Z")
    def test_catalogue_creates_complete_name(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Right."""
        catalogue = Catalogue(seeded_database)

        orchard = catalogue.get_source(
            "Orchard",
            "growing-area",
        )
        root_cellar = catalogue.get_source(
            "Root Cellar",
            "storage-area",
        )

        assert orchard is not None
        assert root_cellar is not None

        name = Name(
            value="nectarine",
            description="A test stone fruit.",
            tags=(
                "fruit",
                "stone-fruit",
            ),
            sources=(
                orchard,
                root_cellar,
            ),
        )

        created = catalogue.create_name(name)

        assert created.value == "nectarine"
        assert created.description == "A test stone fruit."
        assert created.enabled is True
        assert created.state == NameState.AVAILABLE
        assert created.tags == (
            "fruit",
            "stone-fruit",
        )
        assert tuple(source.title for source in created.sources) == (
            "Orchard",
            "Root Cellar",
        )

        history = catalogue.name_history("nectarine")

        assert len(history) == 1

        event = history[0]

        assert event.name == "nectarine"
        assert event.event == NameEventType.CREATED
        assert event.state == NameState.AVAILABLE
        assert event.assigned_to is None
        assert event.occurred_at == datetime(
            2026,
            9,
            20,
            16,
            0,
            tzinfo=UTC,
        )

    def test_catalogue_creates_minimal_name(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Boundary."""
        catalogue = Catalogue(seeded_database)

        created = catalogue.create_name(
            Name(
                value="radicchio",
            )
        )

        assert created.value == "radicchio"
        assert created.tags == ()
        assert created.sources == ()
        assert created.state == NameState.AVAILABLE

    def test_catalogue_commits_complete_name(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Boundary."""
        catalogue = Catalogue(seeded_database)

        catalogue.create_name(
            Name(
                value="radicchio",
            )
        )

        seeded_database.rollback()

        persisted = catalogue.get_name("radicchio")

        assert persisted is not None
        assert persisted.value == "radicchio"

    def test_catalogue_rejects_duplicate_name(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Error."""
        catalogue = Catalogue(seeded_database)

        with pytest.raises(NameAlreadyExistsError):
            catalogue.create_name(
                Name(
                    value="apple",
                    description="Not the seeded apple.",
                )
            )

        existing = catalogue.get_name("apple")

        assert existing is not None
        assert existing.description == ("Test fruit entry for apple.")

    def test_catalogue_creates_missing_source(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Right and Boundary."""
        catalogue = Catalogue(seeded_database)

        source = Source(
            title="Tropical Garden",
            description="A warm growing area.",
            type="growing-area",
        )

        created = catalogue.create_name(
            Name(
                value="dragonfruit",
                sources=(source,),
            )
        )

        assert created.value == "dragonfruit"
        assert created.sources == (source,)

        persisted_source = catalogue.get_source(
            "Tropical Garden",
            "growing-area",
        )

        assert persisted_source == source

    def test_catalogue_reuses_existing_source(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Boundary."""
        catalogue = Catalogue(seeded_database)

        source = catalogue.get_source(
            "Orchard",
            "growing-area",
        )

        assert source is not None

        created = catalogue.create_name(
            Name(
                value="nectarine",
                sources=(source,),
            )
        )

        assert created.sources == (source,)

        sources = catalogue.list_sources(
            title="Orchard",
            source_type="growing-area",
        )

        assert len(sources) == 1

    def test_catalogue_rolls_back_partial_creation(
        self,
        seeded_database: sqlite3.Connection,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """R-BICEP: Error and Boundary."""
        catalogue = Catalogue(seeded_database)

        orchard = catalogue.get_source(
            "Orchard",
            "growing-area",
        )

        assert orchard is not None

        def fail_add_tags(
            name: Name,
            tags: tuple[str, ...],
        ) -> Name:
            raise RuntimeError("forced fixture failure")

        monkeypatch.setattr(
            catalogue.names,
            "add_tags",
            fail_add_tags,
        )

        name = Name(
            value="nectarine",
            tags=("fruit",),
            sources=(orchard,),
        )

        with pytest.raises(
            RuntimeError,
            match="forced fixture failure",
        ):
            catalogue.create_name(name)

        name_row = seeded_database.execute(
            """
            select name
            from names
            where name = ?
            """,
            ("nectarine",),
        ).fetchone()

        event_rows = seeded_database.execute(
            """
            select event
            from name_events
            where name = ?
            """,
            ("nectarine",),
        ).fetchall()

        tag_rows = seeded_database.execute(
            """
            select tag
            from tags
            where name = ?
            """,
            ("nectarine",),
        ).fetchall()

        assert name_row is None
        assert event_rows == []
        assert tag_rows == []

    def test_catalogue_rolls_back_created_source(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Boundary."""
        catalogue = Catalogue(seeded_database)

        source = Source(
            title="Secret Garden",
            description="Created as part of a failed name.",
            type="growing-area",
        )

        with pytest.raises(NameAlreadyExistsError):
            catalogue.create_name(
                Name(
                    value="apple",
                    sources=(source,),
                )
            )

        persisted = catalogue.get_source(
            "Secret Garden",
            "growing-area",
        )

        assert persisted is None


class TestNameHistoryCatalogue:
    """Test lifecycle history orchestration."""

    def test_catalogue_returns_history_in_order(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Right."""
        catalogue = Catalogue(seeded_database)

        history = catalogue.name_history("cherry")

        assert tuple(event.event for event in history) == (
            NameEventType.CREATED,
            NameEventType.ALLOCATED,
            NameEventType.RELEASED,
        )

        assert tuple(event.state for event in history) == (
            NameState.AVAILABLE,
            NameState.ALLOCATED,
            NameState.AVAILABLE,
        )

    def test_catalogue_history_rejects_missing_name(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Error."""
        catalogue = Catalogue(seeded_database)

        with pytest.raises(NameNotFoundError):
            catalogue.name_history("dragonfruit")


class TestAllocateNameCatalogue:
    """Test name allocation orchestration."""

    @freeze_time("2026-09-20T17:00:00Z")
    def test_catalogue_allocates_available_name(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Right."""
        catalogue = Catalogue(seeded_database)

        event = catalogue.allocate_name(
            "apricot",
            "server-01",
        )

        assert event.name == "apricot"
        assert event.assigned_to == "server-01"
        assert event.event == NameEventType.ALLOCATED
        assert event.state == NameState.ALLOCATED
        assert event.occurred_at == datetime(
            2026,
            9,
            20,
            17,
            0,
            tzinfo=UTC,
        )

        name = catalogue.get_name("apricot")

        assert name is not None
        assert name.state == NameState.ALLOCATED

        history = catalogue.name_history("apricot")

        assert history[-1] == event

    @pytest.mark.parametrize(
        "value",
        [
            pytest.param(
                "apple",
                id="already_allocated",
            ),
            pytest.param(
                "blueberry",
                id="reserved",
            ),
        ],
    )
    def test_catalogue_rejects_unavailable_allocation(
        self,
        seeded_database: sqlite3.Connection,
        value: str,
    ) -> None:
        """R-BICEP: Error."""
        catalogue = Catalogue(seeded_database)

        with pytest.raises(InvalidNameTransitionError):
            catalogue.allocate_name(
                value,
                "server-01",
            )

    def test_catalogue_rejects_disabled_allocation(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Boundary."""
        catalogue = Catalogue(seeded_database)

        with pytest.raises(InvalidNameTransitionError):
            catalogue.allocate_name(
                "lime",
                "server-01",
            )

    @pytest.mark.parametrize(
        "assigned_to",
        [
            "",
            "   ",
        ],
    )
    def test_catalogue_rejects_empty_allocation_target(
        self,
        seeded_database: sqlite3.Connection,
        assigned_to: str,
    ) -> None:
        """R-BICEP: Error."""
        catalogue = Catalogue(seeded_database)

        with pytest.raises(
            ValueError,
            match="assigned_to must not be empty",
        ):
            catalogue.allocate_name(
                "apricot",
                assigned_to,
            )

    def test_catalogue_rejects_missing_allocation_name(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Error."""
        catalogue = Catalogue(seeded_database)

        with pytest.raises(NameNotFoundError):
            catalogue.allocate_name(
                "dragonfruit",
                "server-01",
            )


class TestReserveNameCatalogue:
    """Test name reservation orchestration."""

    @freeze_time("2026-09-20T17:15:00Z")
    def test_catalogue_reserves_available_name(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Right."""
        catalogue = Catalogue(seeded_database)

        event = catalogue.reserve_name(
            "blackberry",
            "future-server",
        )

        assert event.name == "blackberry"
        assert event.assigned_to == "future-server"
        assert event.event == NameEventType.RESERVED
        assert event.state == NameState.RESERVED

        name = catalogue.get_name("blackberry")

        assert name is not None
        assert name.state == NameState.RESERVED

    @pytest.mark.parametrize(
        "value",
        [
            pytest.param(
                "apple",
                id="allocated",
            ),
            pytest.param(
                "blueberry",
                id="already_reserved",
            ),
        ],
    )
    def test_catalogue_rejects_unavailable_reservation(
        self,
        seeded_database: sqlite3.Connection,
        value: str,
    ) -> None:
        """R-BICEP: Error."""
        catalogue = Catalogue(seeded_database)

        with pytest.raises(InvalidNameTransitionError):
            catalogue.reserve_name(
                value,
                "future-server",
            )

    def test_catalogue_rejects_disabled_reservation(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Boundary."""
        catalogue = Catalogue(seeded_database)

        with pytest.raises(InvalidNameTransitionError):
            catalogue.reserve_name(
                "turnip",
                "future-server",
            )

    @pytest.mark.parametrize(
        "assigned_to",
        [
            "",
            "   ",
        ],
    )
    def test_catalogue_rejects_empty_reservation_target(
        self,
        seeded_database: sqlite3.Connection,
        assigned_to: str,
    ) -> None:
        """R-BICEP: Error."""
        catalogue = Catalogue(seeded_database)

        with pytest.raises(
            ValueError,
            match="assigned_to must not be empty",
        ):
            catalogue.reserve_name(
                "blackberry",
                assigned_to,
            )

    def test_catalogue_rejects_missing_reservation_name(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Error."""
        catalogue = Catalogue(seeded_database)

        with pytest.raises(NameNotFoundError):
            catalogue.reserve_name(
                "dragonfruit",
                "future-server",
            )


class TestReleaseNameCatalogue:
    """Test release orchestration."""

    @pytest.mark.parametrize(
        ("value", "assigned_to"),
        [
            pytest.param(
                "apple",
                "device-01",
                id="allocated",
            ),
            pytest.param(
                "blueberry",
                "device-02",
                id="reserved",
            ),
        ],
    )
    def test_catalogue_releases_unavailable_name(
        self,
        seeded_database: sqlite3.Connection,
        value: str,
        assigned_to: str,
    ) -> None:
        """R-BICEP: Right."""
        catalogue = Catalogue(seeded_database)

        event = catalogue.release_name(value)

        assert event.name == value
        assert event.event == NameEventType.RELEASED
        assert event.state == NameState.AVAILABLE
        assert event.assigned_to is None

        name = catalogue.get_name(value)

        assert name is not None
        assert name.state == NameState.AVAILABLE

    def test_catalogue_release_preserves_assignment_history(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Boundary."""
        catalogue = Catalogue(seeded_database)

        catalogue.release_name("apple")

        history = catalogue.name_history("apple")

        assert history[-2].event == NameEventType.ALLOCATED
        assert history[-2].assigned_to == "device-01"

        assert history[-1].event == NameEventType.RELEASED
        assert history[-1].assigned_to is None
        assert history[-1].state == NameState.AVAILABLE

    def test_catalogue_rejects_release_of_available_name(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Boundary."""
        catalogue = Catalogue(seeded_database)

        with pytest.raises(InvalidNameTransitionError):
            catalogue.release_name("apricot")

    def test_catalogue_rejects_release_of_missing_name(
        self,
        seeded_database: sqlite3.Connection,
    ) -> None:
        """R-BICEP: Error."""
        catalogue = Catalogue(seeded_database)

        with pytest.raises(NameNotFoundError):
            catalogue.release_name("dragonfruit")
