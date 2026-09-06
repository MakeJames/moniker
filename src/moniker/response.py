"""Response definitions for the Moniker package."""

from datetime import datetime
from typing import Any, Generic, override, Self, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Link(BaseModel):
    """Base model for links within the json response.

    Links maintain the self discoverability of the api.
    """

    href: str
    rel: str
    type: str = "application/json"
    title: str | None = None

    @classmethod
    def self_link(
        cls,
        href: str,
        *,
        type: str = "application/json",
        title: str | None = None,
    ) -> Self:
        """Build a reference to the current object."""
        return cls(href=href, rel="self", type=type, title=title)


class LinkedResource(BaseModel):
    """A container for links related to a resource."""

    links: tuple[Link, ...] = ()


class Document(LinkedResource):
    """A page within the api."""

    title: str
    description: str | None = None


class Collection(Document, Generic[T]):
    """A collection of items within the api."""

    count: int = Field(ge=0)
    items: tuple[T, ...] = ()
    ...


class ApplicationRoot(Document):
    """The root document of the applicaiton."""

    version: str


class NameResource(Document):
    """A name item from the database."""

    sources: tuple[Link, ...] = ()
    tags: tuple[str, ...] = ()
    in_use: bool = False

    @override
    def model_post_init(self, __context: Any) -> None:
        """Dynamically add the links to each name."""
        if not self.links:
            self.links = (
                Link.self_link(f"/names/{self.title}", title=self.title),
            )


class SourceResource(Document):
    """The source material for a catelogue item."""

    type: str
    items: int = Field(ge=0)
    names: tuple[NameResource, ...] = ()

    @override
    def model_post_init(self, __context: Any) -> None:
        """Dynamically add the links to each name."""
        if not self.links:
            self.links = (
                Link.self_link(f"/sources/{self.title}", title=self.title),
            )


class SourceCollection(Document):
    """A Collection of Sources."""

    count: int = Field(ge=0)
    items: tuple[Link, ...] = ()

    @override
    def model_post_init(self, __context: Any) -> None:
        """Dynamically add the links to each name."""
        if not self.links:
            self.links = (Link.self_link("/sources", title=self.title),)


class NameCollection(Collection[NameResource]):
    """A collection of Names."""

    pass


class TagResource(Document):
    """A Tag and meta data abaout the tag."""

    count: int = Field(ge=0)

    @override
    def model_post_init(self, __context: Any) -> None:
        """Dynamically add the links to each tag."""
        if not self.links:
            self.links = (
                Link.self_link(f"/tags/{self.title}", title=self.title),
            )


class TagCollection(Collection[TagResource]):
    """A collection of Tags."""

    pass


class AllocationResource(Document):
    """The record of a name given to a specific device or application."""

    assigned_to: str
    assigned_at: datetime
    released_at: datetime | None = None

    @override
    def model_post_init(self, __context: Any) -> None:
        """Dynamically add the links to each allocation."""
        if not self.links:
            self.links = (
                Link.self_link(
                    f"/allocations/{self.title}",
                    title=self.title,
                ),
            )


class AllocationCollection(Collection[AllocationResource]):
    """A collection of Allocations."""

    pass


class Suggestion(Document):
    """The response constructor for a suggestion."""

    name: NameResource
    query: str | None = None

    @override
    def model_post_init(self, __context: Any) -> None:
        """Dynamically add the links to each name."""
        if self.query:
            self.links = (Link.self_link(f"/names/suggest?{self.query}"),)
        else:
            self.links = (Link.self_link("/names/suggest"),)
