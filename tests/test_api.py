"""Test the api routes."""

import pytest

from fastapi import status
from fastapi.testclient import TestClient


from moniker.app import app


def test_application_starts() -> None:
    """R-BICEP: Right."""
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "status": "ok",
    }


def test_application_root() -> None:
    """R-BICEP: Right."""
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("title") == "Moniker"
    assert response.json().get("version") == "0.1"


@pytest.mark.parametrize(
    ("query", "expected_count"),
    [
        pytest.param(
            "",
            5,
            id="all_sources",
        ),
        pytest.param(
            "?source_type=growing-area",
            4,
            id="filters_by_type",
        ),
        pytest.param(
            "?title=Orchard",
            1,
            id="filters_by_title",
        ),
        pytest.param(
            "?title=Orchard&source_type=growing-area",
            1,
            id="filters_by_title_and_type",
        ),
        pytest.param(
            "?source_type=market",
            0,
            id="no_matches",
        ),
    ],
)
def test_list_sources(
    api_client: TestClient,
    query: str,
    expected_count: int,
) -> None:
    """R-BICEP: Right."""
    response = api_client.get(f"/sources{query}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == expected_count


@pytest.mark.parametrize(
    ("path", "expected_title", "expected_type"),
    [
        pytest.param(
            "/sources/growing-area/Orchard",
            "Orchard",
            "growing-area",
            id="orchard",
        ),
        pytest.param(
            "/sources/growing-area/Kitchen%20Garden",
            "Kitchen Garden",
            "growing-area",
            id="encoded_title",
        ),
        pytest.param(
            "/sources/storage-area/Root%20Cellar",
            "Root Cellar",
            "storage-area",
            id="storage_source",
        ),
    ],
)
def test_get_source(
    api_client: TestClient,
    path: str,
    expected_title: str,
    expected_type: str,
) -> None:
    """R-BICEP: Right."""
    response = api_client.get(path)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["title"] == expected_title
    assert response.json()["type"] == expected_type


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param(
            {
                "title": "",
                "type": "book",
            },
            id="empty_title",
        ),
        pytest.param(
            {
                "title": "   ",
                "type": "book",
            },
            id="whitespace_title",
        ),
        pytest.param(
            {
                "title": "Earthsea",
                "type": "",
            },
            id="empty_type",
        ),
        pytest.param(
            {
                "title": "Earthsea",
                "type": "   ",
            },
            id="whitespace_type",
        ),
        pytest.param(
            {
                "type": "book",
            },
            id="missing_title",
        ),
        pytest.param(
            {
                "title": "Earthsea",
            },
            id="missing_type",
        ),
    ],
)
def test_create_source_rejects_invalid_payload(
    api_client: TestClient,
    payload: dict[str, str],
) -> None:
    """R-BICEP: Error."""
    response = api_client.post(
        "/sources",
        json=payload,
    )

    assert response.status_code == (status.HTTP_422_UNPROCESSABLE_CONTENT)


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param(
            {
                "title": "Orchard",
                "description": None,
                "type": "growing-area",
            },
            id="existing_growing_area_source",
        ),
        pytest.param(
            {
                "title": "Root Cellar",
                "description": "Different description.",
                "type": "storage-area",
            },
            id="duplicate_identity_different_metadata",
        ),
    ],
)
def test_create_source_rejects_duplicate(
    api_client: TestClient,
    payload: dict[str, str | None],
) -> None:
    """R-BICEP: Error."""
    response = api_client.post(
        "/sources",
        json=payload,
    )

    assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param(
            {
                "title": "Polytunnel",
                "description": "A covered growing area.",
                "type": "growing-area",
            },
            id="with_description",
        ),
        pytest.param(
            {
                "title": "Market Stall",
                "description": None,
                "type": "market",
            },
            id="without_description",
        ),
    ],
)
def test_create_source(
    api_client: TestClient,
    payload: dict[str, str | None],
) -> None:
    """R-BICEP: Right."""
    response = api_client.post(
        "/sources",
        json=payload,
    )

    assert response.status_code == status.HTTP_201_CREATED

    body = response.json()

    assert body["title"] == payload["title"]
    assert body["description"] == payload["description"]
    assert body["type"] == payload["type"]

    assert response.headers["location"]


def test_create_source_persists_between_requests(
    api_client: TestClient,
) -> None:
    """R-BICEP: Boundary."""
    payload = {
        "title": "Earthsea",
        "description": "A fantasy setting.",
        "type": "book",
    }

    create_response = api_client.post(
        "/sources",
        json=payload,
    )

    location = create_response.headers["location"]

    get_response = api_client.get(location)

    assert get_response.status_code == status.HTTP_200_OK
    assert get_response.json()["title"] == "Earthsea"
