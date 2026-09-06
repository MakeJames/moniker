"""Test the domain models."""

import pytest
from pydantic import ValidationError

from moniker.domain import Name, NameEventType, NameState, Source


def test_name_defaults_to_available() -> None:
    """R-BICEP: Right."""
    name = Name(value="calcifer")

    assert name.state is NameState.AVAILABLE
    assert name.enabled is True
    assert name.tags == ()
    assert name.sources == ()


@pytest.mark.parametrize(
    ("event", "value"),
    [
        (NameState.AVAILABLE, "available"),
        (NameState.ALLOCATED, "allocated"),
        (NameState.RESERVED, "reserved"),
    ],
)
def test_allocation_state_values(
    event: NameState,
    value: str,
) -> None:
    """R-BICEP: Right."""
    assert event.value == value


@pytest.mark.parametrize(
    ("event", "value"),
    [
        (NameEventType.CREATED, "created"),
        (NameEventType.ALLOCATED, "allocated"),
        (NameEventType.RESERVED, "reserved"),
        (NameEventType.RELEASED, "released"),
    ],
)
def test_allocation_event_type_values(
    event: NameEventType,
    value: str,
) -> None:
    """R-BICEP: Right."""
    assert event.value == value


def test_source_is_immutable() -> None:
    """R-BICEP: Boundary."""
    source = Source(
        title="Doctor Who",
        type="television",
    )

    with pytest.raises(ValidationError):
        source.title = "Dr Who"


def test_name_can_have_multiple_sources() -> None:
    """R-BICEP: Right."""
    name = Name(
        value="atlas",
        sources=(
            Source(
                title="Greek mythology",
                type="mythology",
            ),
            Source(
                title="Portal 2",
                type="game",
            ),
        ),
    )
    sources_count = 2

    assert len(name.sources) == sources_count
    assert name.sources[0].title == "Greek mythology"
    assert name.sources[1].type == "game"
