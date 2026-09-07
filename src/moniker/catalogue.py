"""Application orchestration for the Moniker catalogue.

Coordinate operations across the domain and persistence layers.

The catalogue layer owns application-level operations
that may involve one or more persistence stores.

It is responsible for:

- coordinating persistence operations
- managing transaction boundaries
- preserving application-level invariants
- returning domain objects to callers

Classes:

    Catalogue:
        coordinates operations across catalogue stores

    SourceAlreadyExistsError:
        Database error when attempting to create an existing resource.


"""

from sqlite3 import Connection, IntegrityError


from moniker.domain import Source
from moniker.stores import SourceStore


class SourceAlreadyExistsError(Exception):
    """Raised when attempting to create an existing source."""


class Catalogue:
    """Coordinate operations across Moniker's catalogue.

    Stores are responsible for reading and mutating their own persisted data.
    The catalogue combines those operations into complete application actions
    and controls the transaction boundary around mutations.

    A single database connection is shared between the catalogue
    and its stores so that operations involving multiple stores
    can participate in the same transaction.

    Methods:
        list_sources:
            Fetch sources matching optional catalogue filters.

        get_source:
            Fetch a source by its composite identity.

        create_source:
            Create a source as a single transactional operation.

    """

    def __init__(self, connection: Connection) -> None:
        """Instantiate the catalogue and its persistence stores."""
        self.connection = connection
        self.sources = SourceStore(connection)

    def list_sources(
        self,
        *,
        title: str | None = None,
        source_type: str | None = None,
    ) -> tuple[Source, ...]:
        """Fetch sources matching the supplied filters."""
        return self.sources.list(
            title=title,
            source_type=source_type,
        )

    def get_source(
        self,
        title: str,
        source_type: str,
    ) -> Source | None:
        """Fetch a source by its composite identity."""
        return self.sources.get(
            title,
            source_type,
        )

    def create_source(
        self,
        source: Source,
    ) -> Source:
        """Create a source within a managed transaction."""
        try:
            with self.connection:
                return self.sources.create(source)
        except IntegrityError as error:
            raise SourceAlreadyExistsError(
                f"Source already exists: {source.title} ({source.type})"
            ) from error
