"""Test the api routes."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from moniker.app import app


def response_titles(
    response: dict[str, object],
) -> tuple[str, ...]:
    """Return titles from an API collection response."""
    items = response["items"]

    assert isinstance(items, list)

    return tuple(item["title"] for item in items)


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

    assert response.status_code == (status.HTTP_200_OK)

    body = response.json()

    assert body["title"] == "Moniker"
    assert body["version"] == "0.1"

    hrefs = tuple(link["href"] for link in body["links"])

    assert "/names" in hrefs
    assert "/sources" in hrefs
    assert "/suggestion" in hrefs


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


def test_get_source_returns_not_found(
    api_client: TestClient,
) -> None:
    """R-BICEP: Boundary."""
    response = api_client.get("/sources/growing-area/Does%20Not%20Exist")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": "Source not found",
    }


class TestNameApi:
    """Test catalogue name routes."""

    @pytest.mark.parametrize(
        ("query", "expected"),
        [
            pytest.param(
                "?query=berry",
                (
                    "blackberry",
                    "blueberry",
                    "strawberry",
                ),
                id="query",
            ),
            pytest.param(
                "?query=berry&state=available",
                (
                    "blackberry",
                    "strawberry",
                ),
                id="query_and_state",
            ),
            pytest.param(
                "?tag=fruit&tag=orchard&state=available",
                (
                    "apricot",
                    "cherry",
                    "peach",
                    "pear",
                    "plum",
                ),
                id="tags_and_state",
            ),
            pytest.param(
                "?enabled=false",
                (
                    "lime",
                    "turnip",
                ),
                id="disabled",
            ),
        ],
    )
    def test_list_names(
        self,
        api_client: TestClient,
        query: str,
        expected: tuple[str, ...],
    ) -> None:
        """R-BICEP: Right and Boundary."""
        response = api_client.get(f"/names{query}")

        assert response.status_code == (status.HTTP_200_OK)

        body = response.json()

        assert body["count"] == len(expected)
        assert tuple(item["title"] for item in body["items"]) == expected

    def test_get_name(
        self,
        api_client: TestClient,
    ) -> None:
        """R-BICEP: Right."""
        response = api_client.get("/names/apple")

        assert response.status_code == (status.HTTP_200_OK)

        body = response.json()

        assert body["title"] == "apple"
        assert body["state"] == "allocated"
        assert body["enabled"] is True
        assert body["tags"] == [
            "fruit",
            "orchard",
            "storage",
            "sweet",
        ]

    def test_get_name_returns_not_found(
        self,
        api_client: TestClient,
    ) -> None:
        """R-BICEP: Boundary."""
        response = api_client.get("/names/dragonfruit")

        assert response.status_code == (status.HTTP_404_NOT_FOUND)

    def test_create_name(
        self,
        api_client: TestClient,
    ) -> None:
        """R-BICEP: Right."""
        response = api_client.post(
            "/names",
            json={
                "value": "dragonfruit",
            },
        )

        assert response.status_code == (status.HTTP_201_CREATED)

        body = response.json()

        assert body["title"] == "dragonfruit"
        assert body["state"] == "available"
        assert body["enabled"] is True

        assert response.headers["location"] == ("/names/dragonfruit")

        persisted = api_client.get(response.headers["location"])

        assert persisted.status_code == (status.HTTP_200_OK)
        assert persisted.json()["title"] == ("dragonfruit")

    def test_create_name_rejects_duplicate(
        self,
        api_client: TestClient,
    ) -> None:
        """R-BICEP: Error."""
        response = api_client.post(
            "/names",
            json={
                "value": "apple",
            },
        )

        assert response.status_code == (status.HTTP_409_CONFLICT)

    @pytest.mark.parametrize(
        "value",
        [
            "",
            "   ",
        ],
    )
    def test_create_name_rejects_empty_value(
        self,
        api_client: TestClient,
        value: str,
    ) -> None:
        """R-BICEP: Error."""
        response = api_client.post(
            "/names",
            json={
                "value": value,
            },
        )

        assert response.status_code == (status.HTTP_422_UNPROCESSABLE_CONTENT)


class TestSuggestionApi:
    """Test name suggestion routes."""

    @pytest.mark.parametrize(
        ("query", "expected"),
        [
            pytest.param(
                "?tag=brassica&tag=leafy",
                "cabbage",
                id="tags",
            ),
            pytest.param(
                "?tag=storage&source_title=Orchard",
                "pear",
                id="tag_and_source",
            ),
        ],
    )
    def test_suggest_name(
        self,
        api_client: TestClient,
        query: str,
        expected: str,
    ) -> None:
        """R-BICEP: Right."""
        response = api_client.get(f"/suggestion{query}")

        assert response.status_code == (status.HTTP_200_OK)

        body = response.json()

        assert body["name"]["title"] == expected
        assert body["name"]["state"] == "available"
        assert body["name"]["enabled"] is True

    def test_suggestion_returns_not_found(
        self,
        api_client: TestClient,
    ) -> None:
        """R-BICEP: Boundary."""
        response = api_client.get("/suggestion?tag=citrus")

        assert response.status_code == (status.HTTP_404_NOT_FOUND)


class TestNameHistoryApi:
    """Test name lifecycle history routes."""

    def test_get_name_history(
        self,
        api_client: TestClient,
    ) -> None:
        """R-BICEP: Right."""
        response = api_client.get("/names/cherry/history")

        assert response.status_code == (status.HTTP_200_OK)

        body = response.json()

        cherry_history_events = 3

        assert body["count"] == cherry_history_events

        assert tuple(item["event"] for item in body["items"]) == (
            "created",
            "allocated",
            "released",
        )

        assert tuple(item["state"] for item in body["items"]) == (
            "available",
            "allocated",
            "available",
        )

        assert body["items"][-1]["assigned_to"] is None

    def test_missing_name_history_returns_not_found(
        self,
        api_client: TestClient,
    ) -> None:
        """R-BICEP: Boundary."""
        response = api_client.get("/names/dragonfruit/history")

        assert response.status_code == (status.HTTP_404_NOT_FOUND)


class TestNameLifecycleApi:
    """Test allocation lifecycle routes."""

    @pytest.mark.parametrize(
        (
            "name",
            "operation",
            "assigned_to",
            "expected_event",
            "expected_state",
        ),
        [
            pytest.param(
                "apricot",
                "allocate",
                "server-01",
                "allocated",
                "allocated",
                id="allocate",
            ),
            pytest.param(
                "blackberry",
                "reserve",
                "future-server",
                "reserved",
                "reserved",
                id="reserve",
            ),
        ],
    )
    def test_assign_name(
        self,
        api_client: TestClient,
        name: str,
        operation: str,
        assigned_to: str,
        expected_event: str,
        expected_state: str,
    ) -> None:
        """R-BICEP: Right."""
        response = api_client.post(
            f"/names/{name}/{operation}",
            json={
                "assigned_to": assigned_to,
            },
        )

        assert response.status_code == (status.HTTP_201_CREATED)

        body = response.json()

        assert body["title"] == name
        assert body["event"] == expected_event
        assert body["state"] == expected_state
        assert body["assigned_to"] == assigned_to

        current = api_client.get(f"/names/{name}")

        assert current.json()["state"] == (expected_state)

    def test_release_name(
        self,
        api_client: TestClient,
    ) -> None:
        """R-BICEP: Right."""
        response = api_client.post("/names/apple/release")

        assert response.status_code == (status.HTTP_201_CREATED)

        body = response.json()

        assert body["event"] == "released"
        assert body["state"] == "available"
        assert body["assigned_to"] is None

        current = api_client.get("/names/apple")

        assert current.json()["state"] == ("available")

    @pytest.mark.parametrize(
        ("path", "payload"),
        [
            pytest.param(
                "/names/apple/allocate",
                {
                    "assigned_to": "server-01",
                },
                id="allocate_allocated",
            ),
            pytest.param(
                "/names/blueberry/reserve",
                {
                    "assigned_to": "server-01",
                },
                id="reserve_reserved",
            ),
            pytest.param(
                "/names/apricot/release",
                None,
                id="release_available",
            ),
        ],
    )
    def test_invalid_transition_returns_conflict(
        self,
        api_client: TestClient,
        path: str,
        payload: dict[str, str] | None,
    ) -> None:
        """R-BICEP: Error."""
        response = api_client.post(
            path,
            json=payload,
        )

        assert response.status_code == (status.HTTP_409_CONFLICT)

    @pytest.mark.parametrize(
        "assigned_to",
        [
            "",
            "   ",
        ],
    )
    def test_assignment_rejects_empty_target(
        self,
        api_client: TestClient,
        assigned_to: str,
    ) -> None:
        """R-BICEP: Error."""
        response = api_client.post(
            "/names/apricot/allocate",
            json={
                "assigned_to": assigned_to,
            },
        )

        assert response.status_code == (status.HTTP_422_UNPROCESSABLE_CONTENT)

    def test_lifecycle_missing_name_returns_not_found(
        self,
        api_client: TestClient,
    ) -> None:
        """R-BICEP: Error."""
        response = api_client.post(
            "/names/dragonfruit/allocate",
            json={
                "assigned_to": "server-01",
            },
        )

        assert response.status_code == (status.HTTP_404_NOT_FOUND)
