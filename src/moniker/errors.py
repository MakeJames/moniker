"""HTTP error handling for the Moniker API.

Translate application-layer exceptions into HTTP responses
and describe common error responses exposed by API routes.

This module is responsible for:

mapping catalogue exceptions to HTTP status codes
defining reusable API error response descriptions

It does not:

implement catalogue behaviour
access persistence stores
manage database transactions

"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from moniker.catalogue import SourceAlreadyExistsError


class ErrorResponse(BaseModel):
    """A standard error returned by the Moniker API."""

    detail: str


SOURCE_NOT_FOUND_RESPONSE = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": "The requested source does not exist.",
    },
}

SOURCE_CREATE_RESPONSES = {
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": "A source with this title and type already exists.",
    },
}


def register_exception_handlers(app: FastAPI) -> None:
    """Register application exception handlers with FastAPI."""

    @app.exception_handler(SourceAlreadyExistsError)
    async def source_already_exists(
        request: Request,
        error: SourceAlreadyExistsError,
    ) -> JSONResponse:
        """Return a conflict when a source already exists."""
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": str(error),
            },
        )
