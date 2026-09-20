"""Persist and retrieve catalogue lifecycle events."""

from sqlite3 import Connection, Row

from moniker.domain import NameEvent, NameEventType, NameState
from moniker.utils import to_utc_string


class NameEventStore:
    """Persist and retrieve append-only name lifecycle events.

    Lifecycle events record changes to the availability of a catalogue name.

    The store is responsible for:

    - appending lifecycle events
    - retrieving the latest event for a name
    - retrieving the complete lifecycle history for a name

    Events are append-only.
    Existing events must not be updated or deleted.

    Attributes:
        connection:
            An active connection to the database.

    """

    def __init__(
        self,
        connection: Connection,
    ) -> None:
        """Instantiate the store."""
        self.connection = connection

    def append(
        self,
        event: NameEvent,
    ) -> NameEvent:
        """Append an event to a name's lifecycle history."""
        self._validate_query_value(event.name, "name")
        self._validate_query_value(event.assigned_to, "assigned_to")

        query = """
            insert into name_events (
                name,
                assigned_to,
                event,
                state,
                occurred_at
            )
            values (?, ?, ?, ?, ?)
        """

        self.connection.execute(
            query,
            (
                event.name,
                event.assigned_to,
                event.event.value,
                event.state.value,
                to_utc_string(event.occurred_at),
            ),
        )

        return event

    def latest(
        self,
        name: str,
    ) -> NameEvent | None:
        """Return the latest lifecycle event for a name."""
        self._validate_query_value(name, "name")

        row = self.connection.execute(
            """
            select
                name,
                assigned_to,
                event,
                state,
                occurred_at
            from name_events
            where name_events.name = ?
            order by occurred_at desc
            limit 1
            """,
            (name,),
        ).fetchone()

        if row is None:
            return None

        return self._hydrate_event(row)

    def history(
        self,
        name: str,
    ) -> tuple[NameEvent, ...]:
        """Return the lifecycle history for a name."""
        self._validate_query_value(name, "name")

        rows = self.connection.execute(
            """
            select
                name,
                assigned_to,
                event,
                state,
                occurred_at
            from name_events
            where name_events.name = ?
            order by occurred_at
            """,
            (name,),
        ).fetchall()

        return tuple(self._hydrate_event(row) for row in rows)

    @staticmethod
    def _hydrate_event(
        row: Row,
    ) -> NameEvent:
        """Construct a NameEvent from a database row."""
        return NameEvent(
            name=row["name"],
            assigned_to=row["assigned_to"],
            event=NameEventType(row["event"]),
            state=NameState(row["state"]),
            occurred_at=row["occurred_at"],
        )

    @staticmethod
    def _validate_query_value(
        value: str | None,
        field: str,
    ) -> None:
        """Reject empty values while allowing omitted values."""
        if value is not None and not value.strip():
            raise ValueError(f"{field} must not be empty")
