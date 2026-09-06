"""Domain mappings for Moniker."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class NameState(StrEnum):
    """Track the availability of a catalogue entry.

    A catalogue item can be assigned to a device or service.
    This state preserves the current availability of a name.
    """

    AVAILABLE = "available"
    ALLOCATED = "allocated"
    RESERVED = "reserved"


class NameEventType(StrEnum):
    """Track the action or event on a given catalogue entry."""

    CREATED = "created"
    ALLOCATED = "allocated"
    RESERVED = "reserved"
    RELEASED = "released"


class Source(BaseModel):
    """A referenced source in the catalogue.

    The referenced work, person or mythology from which a name is derived.
    A name may appear across multiple sources
    or mythologies.

    Attributes:
        title:
            The canonical title of the given source.

        description:
            Human readable description of the source material or work.

        type:
            The genre or category of Source material.

    """

    model_config = ConfigDict(frozen=True)

    title: str
    description: str | None = None
    type: str | None = None


class Name(BaseModel):
    """The Name object in Moniker's catalogue.

    A name represents a candidate identifier that may be suggested
    and allocated to a device or service.

    Names are persistent catalogue entries,
    they persist beyond allocation.
    A name is considered available when it is enabled
    and has no active allocation.

    The `enabled` flag controls whether the name may participate
    in future suggestions or allocations.
    Disabling a name preserves its metadata
    and allocation history while removing it from circulation.

    Tags describe characteristics that may be used
    when filtering or ranking suggestions.
    They may describe both the role or thematic sources,
    such as `storage` or `network`,
    `fantasy` or `mythology`.

    Attributes:
        value:
            The canonical name used to identify this catalogue entry.

        source:
            The works, persons, mythologies or other references
            from which the name is drawn.

        description:
            Human readable context explaining the reference.

        tags:
            Characteristics associated with the name
            and used to support discovery and suggestion.

        enabled:
            Whether the name is eligible for future suggestions
            and allocation.

        state:
            Whether the name is currently available for future suggestions
            and allocation.

    """

    model_config = ConfigDict(frozen=True)

    value: str
    sources: tuple[Source, ...] = ()
    description: str | None = None
    tags: tuple[str, ...] = ()
    enabled: bool = True
    state: NameState = NameState.AVAILABLE


class NameEvent(BaseModel):
    """An entry in the allocation history for a given name.

    Throughout its lifecycle,
    a name can be assigned, reserved, made available.
    Historical records enhance the meaning
    and context of a given catalogue item.

    These records are available in an append only table.
    To recall the current availability of a name,
    the latest event should be interpreted as the current state.

    Attributes:
        name:
            The name affected by the event.

        assigned_to:
            A reference to the device or service that is attached to the name.

        event:
            The change that was applied to the given name.

        state:
            The current availability of the name.

        occured_at:
            The timestamp of the activity.

    """

    model_config = ConfigDict(frozen=True)

    name: str
    assigend_to: str | None = None
    event: NameEventType
    state: NameState
    occured_at: datetime
