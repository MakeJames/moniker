"""Routes and endpoints for the api."""

from fastapi import FastAPI

from moniker.models import ApplicationRoot, Link


app = FastAPI(title="Moniker", description="A small API for naming things.")


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
        ),
    )


@app.get("/health")
def health() -> dict[str, str]:
    """Lightweight health check endpoint."""
    return {"status": "ok"}
