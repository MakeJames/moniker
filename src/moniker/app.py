"""Routes and endpoints for the api."""

from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, Response, status

from moniker.response import ApplicationRoot, Link

from moniker.dependencies import CatalogueDependency
from moniker.domain import Source
from moniker.errors import (
    SOURCE_CREATE_RESPONSES,
    SOURCE_NOT_FOUND_RESPONSE,
    register_exception_handlers,
)
from moniker.response import SourceCollection, SourceResource
from moniker.response_mapping import source_href, source_resource

SourceFilter = Annotated[
    str | None,
    Query(
        min_length=1,
        pattern=r".*\S.*",
    ),
]

app = FastAPI(title="Moniker", description="A small API for naming things.")

register_exception_handlers(app)


@app.get("/")
def application_landing_page() -> ApplicationRoot:
    """Root end point."""
    return ApplicationRoot(
        title="Moniker",
        description="A small API for discovering and allocating names.",
        version="0.1",
        links=(
            Link.self_link("/"),
            Link(
                href="/health",
                rel="health",
                title="Service health",
            ),
            Link(
                href="/sources",
                rel="entries",
                title="Source material for Moniker entries.",
            ),
        ),
    )


@app.get("/health")
def health() -> dict[str, str]:
    """Lightweight health check endpoint."""
    return {"status": "ok"}


@app.get(
    "/sources",
    responses=SOURCE_CREATE_RESPONSES,
)
def list_sources(
    catalogue: CatalogueDependency,
    title: SourceFilter = None,
    source_type: SourceFilter = None,
) -> SourceCollection:
    """List sources matching the supplied filters."""
    sources = catalogue.list_sources(
        title=title,
        source_type=source_type,
    )

    return SourceCollection(
        title="Sources",
        description="Sources referenced by names in the catalogue.",
        count=len(sources),
        items=tuple(
            Link.self_link(
                source_href(source),
                title=source.title,
            )
            for source in sources
        ),
    )


@app.post(
    "/sources",
    status_code=status.HTTP_201_CREATED,
    responses=SOURCE_CREATE_RESPONSES,
)
def create_source(
    source: Source,
    response: Response,
    catalogue: CatalogueDependency,
) -> SourceResource:
    """Create a source in the catalogue."""
    created = catalogue.create_source(source)

    response.headers["Location"] = source_href(created)

    return source_resource(created)


@app.get(
    "/sources/{source_type}/{title}",
    responses=SOURCE_NOT_FOUND_RESPONSE,
)
def get_source(
    source_type: str,
    title: str,
    catalogue: CatalogueDependency,
) -> SourceResource:
    """Fetch a source by its composite identity."""
    source = catalogue.get_source(
        title=title,
        source_type=source_type,
    )

    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found",
        )

    return source_resource(source)
