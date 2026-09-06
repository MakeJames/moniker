"""Utilities."""

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Effective now date and time."""
    return datetime.now(UTC)


def to_utc_string(value: datetime) -> str:
    """Datetime with Z."""
    if value.tzinfo is None:
        raise ValueError("Datetime must include a timezone")

    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def to_utc_datetime(value: str) -> datetime:
    """Parse timestamp with Z to utc."""
    if not value.endswith("Z"):
        raise ValueError("Stored datetime must be UTC and end with 'Z'")

    return datetime.fromisoformat(value.removesuffix("Z") + "+00:00")


def current_time() -> str:
    """Coerce now to string."""
    return to_utc_string(utc_now())
