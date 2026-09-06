"""Test the Utility methods."""

from datetime import UTC, datetime

import pytest

from freezegun import freeze_time

from moniker.utils import to_utc_datetime, to_utc_string, utc_now


@freeze_time("2026-06-28 20:21:10")
def test_utc_now_returns_current_time_in_utc() -> None:
    """R-BICEP: Right."""
    assert utc_now() == datetime(2026, 6, 28, 20, 21, 10, tzinfo=UTC)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (
            datetime(2024, 3, 26, 10, 28, 31, tzinfo=UTC),
            "2024-03-26T10:28:31Z",
        ),
        (
            datetime(2026, 9, 21, 18, 59, 59, tzinfo=UTC),
            "2026-09-21T18:59:59Z",
        ),
    ],
)
def test_to_utc_string(value: datetime, expected: str) -> None:
    """R-BICEP: Right."""
    assert to_utc_string(value) == expected


@pytest.mark.parametrize(
    ("value"),
    [
        datetime(1997, 6, 12),
        datetime(2023, 4, 20, 10, 3, 20),
    ],
)
def test_error_when_missing_tzinfo_utc_string(value: datetime) -> None:
    """R-BICEP: Error."""
    with pytest.raises(ValueError, match="Datetime must include a timezone"):
        to_utc_string(value)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (
            "2026-08-24T10:00:00Z",
            datetime(2026, 8, 24, 10, 0, 0, tzinfo=UTC),
        ),
        (
            "1998-12-25T14:56:34Z",
            datetime(1998, 12, 25, 14, 56, 34, tzinfo=UTC),
        ),
    ],
)
def test_to_utc_datetime(value: str, expected: datetime) -> None:
    """R-BICEP: Right."""
    assert to_utc_datetime(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        "2026-03-02T10:26:10",
    ],
)
def test_error_when_datetime_is_without_timezone_indicator(value: str) -> None:
    """R-BICEP: Error."""
    with pytest.raises(
        ValueError, match="Stored datetime must be UTC and end with 'Z'"
    ):
        to_utc_datetime(value)
