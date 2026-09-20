"""Request definitions for the Moniker API."""

from pydantic import BaseModel, ConfigDict

from moniker.domain import NonEmptyString, Source


class NameCreate(BaseModel):
    """Request to create a catalogue name."""

    model_config = ConfigDict(frozen=True)

    value: NonEmptyString
    sources: tuple[Source, ...] = ()
    description: str | None = None
    tags: tuple[NonEmptyString, ...] = ()
    enabled: bool = True


class AssignmentRequest(BaseModel):
    """Request to assign or reserve a name."""

    model_config = ConfigDict(frozen=True)

    assigned_to: NonEmptyString
