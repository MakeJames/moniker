"""Routes and endpoints for the api."""

from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, Response, status

from moniker.dependencies import CatalogueDependency
from moniker.domain import Name, NameState, NonEmptyString, Source
from moniker.errors import (
    NAME_CREATE_RESPONSES,
    NAME_NOT_FOUND_RESPONSE,
    NAME_TRANSITION_RESPONSES,
    SOURCE_CREATE_RESPONSES,
    SOURCE_NOT_FOUND_RESPONSE,
    SUGGESTION_NOT_FOUND_RESPONSE,
    register_exception_handlers,
)
from moniker.request import AssignmentRequest, NameCreate
from moniker.response import (
    ApplicationRoot,
    Link,
    NameCollection,
    NameEventCollection,
    NameEventResource,
    NameResource,
    SourceCollection,
    SourceResource,
    Suggestion,
)
from moniker.response_mapping import (
    name_event_resource,
    name_history_href,
    name_href,
    name_resource,
    source_href,
    source_resource,
    suggestion_resource,
)

NameFilter = Annotated[str | None, Query(min_length=1, pattern=r".*\S.*")]

NameQuery = Annotated[str | None, Query(min_length=1, pattern=r".*\S.*")]

TagFilters = Annotated[list[NonEmptyString] | None, Query(alias="tag")]

SourceFilter = Annotated[str | None, Query(min_length=1, pattern=r".*\S.*")]

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
                href="/names",
                rel="entries",
                title="Names in the Moniker catalogue.",
            ),
            Link(
                href="/health",
                rel="health",
                title="Service health.",
            ),
            Link(
                href="/sources",
                rel="entries",
                title="Source material for Moniker entries.",
            ),
            Link(
                href="/suggestion",
                rel="suggestion",
                title="Suggest an available name.",
            ),
        ),
    )


@app.get("/health")
def health() -> dict[str, str]:
    """Lightweight health check endpoint."""
    return {"status": "ok"}


@app.get("/sources")
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


@app.get("/names")
def list_names(
    catalogue: CatalogueDependency,
    query: NameQuery = None,
    tags: TagFilters = None,
    source_title: NameFilter = None,
    source_type: NameFilter = None,
    enabled: bool | None = True,
    state: NameState | None = None,
) -> NameCollection:
    """List names matching the supplied filters."""
    names = catalogue.list_names(
        query=query,
        tags=tuple(tags or ()),
        source_title=source_title,
        source_type=source_type,
        enabled=enabled,
        state=state,
    )

    return NameCollection(
        title="Names",
        description="Names in the Moniker catalogue.",
        count=len(names),
        items=tuple(name_resource(name) for name in names),
        links=(Link.self_link("/names"),),
    )


@app.get(
    "/names/{name}",
    responses=NAME_NOT_FOUND_RESPONSE,
)
def get_name(
    name: str,
    catalogue: CatalogueDependency,
) -> NameResource:
    """Fetch a catalogue name."""
    result = catalogue.get_name(name)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Name not found",
        )

    return name_resource(result)


@app.post(
    "/names",
    status_code=status.HTTP_201_CREATED,
    responses=NAME_CREATE_RESPONSES,
)
def create_name(
    request: NameCreate,
    response: Response,
    catalogue: CatalogueDependency,
) -> NameResource:
    """Create a catalogue name."""
    name = Name(
        value=request.value,
        sources=request.sources,
        description=request.description,
        tags=request.tags,
        enabled=request.enabled,
    )

    created = catalogue.create_name(name)

    response.headers["Location"] = name_href(created)

    return name_resource(created)


@app.get(
    "/names/{name}/history",
    responses=NAME_NOT_FOUND_RESPONSE,
)
def name_history(
    name: str,
    catalogue: CatalogueDependency,
) -> NameEventCollection:
    """Return lifecycle history for a name."""
    events = catalogue.name_history(name)

    return NameEventCollection(
        title=name,
        description=f"Lifecycle history for {name}.",
        count=len(events),
        items=tuple(name_event_resource(event) for event in events),
        links=(Link.self_link(name_history_href(name)),),
    )


@app.post(
    "/names/{name}/allocate",
    status_code=status.HTTP_201_CREATED,
    responses=NAME_TRANSITION_RESPONSES,
)
def allocate_name(
    name: str,
    request: AssignmentRequest,
    catalogue: CatalogueDependency,
) -> NameEventResource:
    """Allocate a catalogue name."""
    event = catalogue.allocate_name(
        name,
        request.assigned_to,
    )

    return name_event_resource(event)


@app.post(
    "/names/{name}/reserve",
    status_code=status.HTTP_201_CREATED,
    responses=NAME_TRANSITION_RESPONSES,
)
def reserve_name(
    name: str,
    request: AssignmentRequest,
    catalogue: CatalogueDependency,
) -> NameEventResource:
    """Reserve a catalogue name."""
    event = catalogue.reserve_name(
        name,
        request.assigned_to,
    )

    return name_event_resource(event)


@app.post(
    "/names/{name}/release",
    status_code=status.HTTP_201_CREATED,
    responses=NAME_TRANSITION_RESPONSES,
)
def release_name(
    name: str,
    catalogue: CatalogueDependency,
) -> NameEventResource:
    """Release a catalogue name."""
    event = catalogue.release_name(name)

    return name_event_resource(event)


@app.get(
    "/suggestion",
    responses=SUGGESTION_NOT_FOUND_RESPONSE,
)
def suggest_name(
    catalogue: CatalogueDependency,
    tags: TagFilters = None,
    source_title: NameFilter = None,
    source_type: NameFilter = None,
) -> Suggestion:
    """Suggest an available catalogue name."""
    requested_tags = tuple(tags or ())

    name = catalogue.suggest_name(
        tags=requested_tags,
        source_title=source_title,
        source_type=source_type,
    )

    if name is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No matching name is available.",
        )

    return suggestion_resource(
        name,
        tags=requested_tags,
        source_title=source_title,
        source_type=source_type,
    )
