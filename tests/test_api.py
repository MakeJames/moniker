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
            4,
            id="all_sources",
        ),
        pytest.param(
            "?source_type=book",
            3,
            id="filters_by_type",
        ),
        pytest.param(
            "?title=Doctor%20Who",
            1,
            id="filters_by_title",
        ),
        pytest.param(
            "?title=Doctor%20Who&source_type=television",
            1,
            id="filters_by_title_and_type",
        ),
        pytest.param(
            "?source_type=film",
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
            "/sources/television/Doctor%20Who",
            "Doctor Who",
            "television",
            id="television_source",
        ),
        pytest.param(
            "/sources/book/His%20Dark%20Materials",
            "His Dark Materials",
            "book",
            id="book_source",
        ),
        pytest.param(
            "/sources/book/Howl%27s%20Moving%20Castle",
            "Howl's Moving Castle",
            "book",
            id="encoded_title",
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
                "title": "Doctor Who",
                "description": None,
                "type": "television",
            },
            id="existing_television_source",
        ),
        pytest.param(
            {
                "title": "His Dark Materials",
                "description": "Different description.",
                "type": "book",
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
                "title": "Earthsea",
                "description": (
                    "A fantasy setting created by Ursula K. Le Guin."
                ),
                "type": "book",
            },
            id="with_description",
        ),
        pytest.param(
            {
                "title": "Greek mythology",
                "description": None,
                "type": "mythology",
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
