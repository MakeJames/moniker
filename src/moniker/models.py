"""Model definitions for the Moniker pacakge."""

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


class Name(Document):
    """A name item from the database."""

    source: str | None = None
    tags: tuple[str, ...] = ()
    in_use: bool = False

    @override
    def model_post_init(self, __context: Any) -> None:
        """Dynamically add the links to each name."""
        if not self.links:
            self.links = (
                Link.self_link(f"/names/{self.title}", title=self.title),
            )


class Names(Collection[Name]):
    """A collection of Names."""

    pass


class Tag(Document):
    """A Tag and meta data abaout the tag."""

    count: int = Field(ge=0)

    @override
    def model_post_init(self, __context: Any) -> None:
        """Dynamically add the links to each tag."""
        if not self.links:
            self.links = (
                Link.self_link(f"/tags/{self.title}", title=self.title),
            )


class Tags(Collection[Tag]):
    """A collection of Tags."""

    pass


class Allocation(Document):
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


class Allocations(Collection[Allocation]):
    """A collection of Allocations."""

    pass


class Suggestion(Document):
    """The response constructor for a suggestion."""

    name: Name
    query: str | None = None

    @override
    def model_post_init(self, __context: Any) -> None:
        """Dynamically add the links to each name."""
        if self.query:
            self.links = (Link.self_link(f"/names/suggest?{self.query}"),)
        else:
            self.links = (Link.self_link("/names/suggest"),)
