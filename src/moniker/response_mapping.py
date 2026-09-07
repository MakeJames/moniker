"""Map Moniker domain objects into API representations.

Translate objects from the domain layer into the response models
exposed by the HTTP API.

This module is responsible for:

- constructing canonical resource URLs
- mapping domain objects to response objects
- constructing links between API resources

It does not:

- retrieve or mutate catalogue data
- manage database transactions
- make HTTP routing decisions

"""

from urllib.parse import quote

from moniker.domain import Source
from moniker.response import Link, SourceResource


def source_href(source: Source) -> str:
    """Build the canonical URL for a source."""
    source_type = quote(source.type, safe="")
    title = quote(source.title, safe="")

    return f"/sources/{source_type}/{title}"


def source_resource(source: Source) -> SourceResource:
    """Map a Source domain object to its API representation."""
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
