"""Routes and endpoints for the api."""

from fastapi import FastAPI


app = FastAPI(title="Moniker", description="A small API for naming things.")


@app.get("/health")
def health() -> dict[str, str]:
    """Lightweight health check endpoint."""
    return {"status": "ok"}
