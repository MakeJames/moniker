"""Test the api routes."""

from fastapi import status
from fastapi.testclient import TestClient


from moniker.app import app


def test_application_starts() -> None:
    """R-BICEP: Right."""
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == status.HTTP_200_SUCCESS
    assert response.json() == {
        "status": "ok",
    }
