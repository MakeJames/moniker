"""Map Moniker domain objects into API representations.

Translate objects from the domain layer into the response models
exposed by the HTTP API.

This module is responsible for:

- constructing canonical resource URLs
- mapping domain objects to response objects
- constructing links between API resources

"""

from urllib.parse import quote, urlencode

from moniker.domain import Name, NameEvent, Source
from moniker.response import (
    Link,
    NameEventResource,
    NameResource,
    SourceResource,
    Suggestion,
)


def source_href(source: Source) -> str:
    """Build the canonical URL for a source."""
    source_type = quote(source.type, safe="")
    title = quote(source.title, safe="")

    return f"/sources/{source_type}/{title}"


def source_resource(
    source: Source,
) -> SourceResource:
    """Map a Source into its API representation."""
    return SourceResource(
        title=source.title,
        description=source.description,
        type=source.type,
        links=(
            Link.self_link(
                source_href(source),
                title=source.title,
            ),
        ),
    )


def name_href(
    name: Name | str,
) -> str:
    """Build the canonical URL for a name."""
    value = name.value if isinstance(name, Name) else name

    return f"/names/{quote(value, safe='')}"


def name_history_href(
    name: Name | str,
) -> str:
    """Build the history URL for a name."""
    return f"{name_href(name)}/history"


def name_resource(
    name: Name,
) -> NameResource:
    """Map a Name into its API representation."""
    return NameResource(
        title=name.value,
        description=name.description,
        sources=tuple(
            Link(
                href=source_href(source),
                rel="source",
                title=source.title,
            )
            for source in name.sources
        ),
        tags=name.tags,
        enabled=name.enabled,
        state=name.state,
        links=(
            Link.self_link(
                name_href(name),
                title=name.value,
            ),
            Link(
                href=name_history_href(name),
                rel="history",
                title=f"{name.value} history",
            ),
        ),
    )


def name_event_resource(
    event: NameEvent,
) -> NameEventResource:
    """Map a NameEvent into its API representation."""
    return NameEventResource(
        title=event.name,
        event=event.event,
        state=event.state,
        assigned_to=event.assigned_to,
        occurred_at=event.occurred_at,
        links=(
            Link(
                href=name_history_href(event.name),
                rel="history",
                title=f"{event.name} history",
            ),
        ),
    )


def suggestion_href(
    *,
    tags: tuple[str, ...] = (),
    source_title: str | None = None,
    source_type: str | None = None,
) -> str:
    """Build a suggestion query URL."""
    query: list[tuple[str, str]] = []

    query.extend(("tag", tag) for tag in tags)

    if source_title is not None:
        query.append(("source_title", source_title))

    if source_type is not None:
        query.append(("source_type", source_type))

    if not query:
        return "/suggestion"

    return "/suggestion?" + urlencode(query)


def suggestion_resource(
    name: Name,
    *,
    tags: tuple[str, ...] = (),
    source_title: str | None = None,
    source_type: str | None = None,
) -> Suggestion:
    """Map a suggested name into an API response."""
    return Suggestion(
        title="Name suggestion",
        description="An available name matching the supplied filters.",
        name=name_resource(name),
        links=(
            Link.self_link(
                suggestion_href(
                    tags=tags,
                    source_title=source_title,
                    source_type=source_type,
                )
            ),
        ),
    )
