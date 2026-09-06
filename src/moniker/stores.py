"""Repository methods for the Moniker catalogue.

Translate the persistence and domain layers.

Classes:

    SourceStore
        reads and mutates sources

    NameStore
        reads and mutates names
        manages name to source relationships

    NameEventStore
        appends and reads lifecycle events

"""

from sqlite3 import Connection

from moniker.domain import Source


class SourceStore:
    """Persist and retrieve sources referenced by catalogue names.

    Sources are shared between catalogue entities.
    This store is responsible for:

    - retrieving sources
    - creating new sources

    Methods:
        get:
            Fetches a Source record if it exists.
            Returns None if the record doesn't exist

        create:
            Creates a new source record.

    """

    def __init__(self, connection: Connection) -> None:
        """Instantiate the class."""
        self.connection = connection

    def list(
        self,
        title: str | None = None,
        source_type: str | None = None,
    ) -> tuple[Source, ...]:
        """Fetch sources matching the supplied filters."""
        self._validate_query_value(title, "title")
        self._validate_query_value(source_type, "source_type")
        query = """
            select
                title,
                description,
                type
            from sources
        """

        filters: list[str] = []
        params: list[str] = []

        if title is not None:
            filters.append("title = ?")
            params.append(title)

        if source_type is not None:
            filters.append("type = ?")
            params.append(source_type)

        if filters:
            query += " where " + " and ".join(filters)

        query += " order by title, type"

        rows = self.connection.execute(
            query,
            params,
        ).fetchall()

        return tuple(
            Source(
                title=row["title"],
                description=row["description"],
                type=row["type"],
            )
            for row in rows
        )

    def get(self, title: str, source_type: str) -> Source | None:
        """Fetch a source by its composite identity."""
        self._validate_query_value(title, "title")
        self._validate_query_value(source_type, "source_type")

        row = self.connection.execute(
            """
            select
                title,
                description,
                type
            from sources
            where title = ?
              and type = ?
            """,
            (
                title,
                source_type,
            ),
        ).fetchone()

        if row is None:
            return None

        return Source(
            title=row["title"],
            description=row["description"],
            type=row["type"],
        )

    def create(self, source: Source) -> Source:
        """Create a new source record."""
        query = """
            insert into sources (
                title,
                description,
                type
            )
            values (?, ?, ?)
        """
        self.connection.execute(
            query,
            (
                source.title,
                source.description,
                source.type,
            ),
        )

        return source

    @staticmethod
    def _validate_query_value(
        value: str | None,
        field: str,
    ) -> None:
        """Reject empty query values while allowing omitted filters."""
        if value is not None and not value.strip():
            raise ValueError(f"{field} must not be empty")
