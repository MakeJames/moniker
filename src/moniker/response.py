"""Response definitions for the Moniker package."""

from datetime import datetime
from typing import Any, Generic, Self, TypeVar, override

from pydantic import BaseModel, Field

from moniker.domain import NameEventType, NameState

T = TypeVar("T")


class Link(BaseModel):
    """A link to a related API resource."""

    title: str | None = None
    href: str
    rel: str
    type: str = "application/json"

    @classmethod
    def self_link(
        cls,
        href: str,
        *,
        type: str = "application/json",
        title: str | None = None,
    ) -> Self:
        """Build a reference to the current resource."""
        return cls(title=title, href=href, rel="self", type=type)


class Document(BaseModel):
    """A document within the API."""

    title: str
    description: str | None = None


class Collection(Document, Generic[T]):
    """A collection of API resources."""

    count: int = Field(ge=0)
    items: tuple[T, ...] = ()
    links: tuple[Link, ...] = ()


class ApplicationRoot(Document):
    """The root document of the application."""

    version: str
    links: tuple[Link, ...] = ()


class NameResource(Document):
    """A name item from the catalogue."""

    sources: tuple[Link, ...] = ()
    tags: tuple[str, ...] = ()
    enabled: bool = True
    state: NameState = NameState.AVAILABLE
    links: tuple[Link, ...] = ()

    @override
    def model_post_init(self, __context: Any) -> None:
        """Add links related to the name."""
        if not self.links:
            self.links = (
                Link.self_link(
                    f"/names/{self.title}",
                    title=self.title,
                ),
                Link(
                    title=f"{self.title} history",
                    href=f"/names/{self.title}/history",
                    rel="history",
                ),
            )


class SourceResource(Document):
    """Source material for a catalogue item."""

    type: str
    links: tuple[Link, ...] = ()

    @override
    def model_post_init(self, __context: Any) -> None:
        """Add links related to the source."""
        if not self.links:
            self.links = (
                Link.self_link(
                    f"/sources/{self.type}/{self.title}",
                    title=self.title,
                ),
            )


class SourceCollection(Document):
    """A collection of sources."""

    count: int = Field(ge=0)
    items: tuple[Link, ...] = ()
    links: tuple[Link, ...] = ()

    @override
    def model_post_init(self, __context: Any) -> None:
        """Add links related to the source collection."""
        if not self.links:
            self.links = (
                Link.self_link(
                    "/sources",
                    title=self.title,
                ),
            )


class SourceTypeCollection(Collection[SourceResource]):
    """A collection of sources of a particular type."""

    @override
    def model_post_init(self, __context: Any) -> None:
        """Add links related to the source type."""
        if not self.links:
            self.links = (
                Link.self_link(
                    f"/sources/{self.title}",
                    title=self.title,
                ),
            )


class NameCollection(Collection[NameResource]):
    """A collection of names."""

    pass


class TagResource(Document):
    """A tag and metadata about its catalogue usage."""

    count: int = Field(ge=0)
    links: tuple[Link, ...] = ()

    @override
    def model_post_init(self, __context: Any) -> None:
        """Add links related to the tag."""
        if not self.links:
            self.links = (
                Link.self_link(
                    f"/tags/{self.title}",
                    title=self.title,
                ),
            )


class TagCollection(Collection[TagResource]):
    """A collection of tags."""

    pass


class NameEventResource(Document):
    """A lifecycle event associated with a name."""

    event: NameEventType
    state: NameState
    assigned_to: str | None = None
    occurred_at: datetime
    links: tuple[Link, ...] = ()


class NameEventCollection(Collection[NameEventResource]):
    """A collection of lifecycle events associated with a name."""

    @override
    def model_post_init(self, __context: Any) -> None:
        """Add links related to the name history."""
        if not self.links:
            self.links = (
                Link.self_link(
                    f"/names/{self.title}/history",
                    title=self.title,
                ),
            )


class AllocationResource(Document):
    """The current allocation of a name."""

    assigned_to: str
    assigned_at: datetime
    links: tuple[Link, ...] = ()

    @override
    def model_post_init(self, __context: Any) -> None:
        """Add links related to the allocation."""
        if not self.links:
            self.links = (
                Link.self_link(
                    f"/allocations/{self.title}",
                    title=self.title,
                ),
            )


class AllocationCollection(Collection[AllocationResource]):
    """A collection of allocations."""

    pass


class Suggestion(Document):
    """A suggested available name."""

    name: NameResource
    links: tuple[Link, ...] = ()
