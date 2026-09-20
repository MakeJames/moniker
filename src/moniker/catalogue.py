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


from moniker.domain import Source, NameState, Name, NameEvent, NameEventType
from moniker.stores import (
    NameEventStore,
    NameStore,
    SourceStore,
    MonikerReadWriteError,
)
from moniker.utils import utc_now


class NameNotFoundError(Exception):
    """Raised when a catalogue name does not exist."""


class NameAlreadyExistsError(Exception):
    """Raised when creating an existing name."""


class InvalidNameTransitionError(Exception):
    """Raised when a lifecycle transition is not permitted."""


class SourceNotFoundError(Exception):
    """Raised when looking to find an existing source."""


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
        self.names = NameStore(connection)
        self.events = NameEventStore(connection)


    def _current_name(
        self,
        value: str,
    ) -> Name:
        """Return an existing name or raise."""
        name = self.names.get(value)

        if name is None:
            raise NameNotFoundError(
                f"Name not found: {value}"
            )

        return name

    def suggest_name(
        self,
        *,
        tags: tuple[str, ...] = (),
        source_title: str | None = None,
        source_type: str | None = None,
    ) -> Name | None:
        """Suggest an available catalogue name."""
        return self.names.pick(
            tags=tags,
            source_title=source_title,
            source_type=source_type,
            enabled=True,
            state=NameState.AVAILABLE,
        )

    def list_names(
        self,
        *,
        tags: tuple[str, ...] = (),
        source_title: str | None = None,
        source_type: str | None = None,
        enabled: bool | None = True,
        state: NameState | None = None,
    ) -> tuple[Name, ...]:
        """Fetch names matching catalogue filters."""
        return self.names.list(
            tags=tags,
            source_title=source_title,
            source_type=source_type,
            enabled=enabled,
            state=state,
        )

    def get_name(
        self,
        name: str,
    ) -> Name | None:
        """Fetch a catalogue name."""
        return self.names.get(name)

    def create_name(
        self,
        name: Name,
    ) -> Name:
        """Create a complete catalogue name."""
        for source in name.sources:
            existing = self.sources.get(
                source.title,
                source.type,
            )

            if existing is None:
                self.sources.create(source)

        try:
            with self.connection:
                self.names.create(name)

                self.events.append(
                    NameEvent(
                        name=name.value,
                        event=NameEventType.CREATED,
                        state=NameState.AVAILABLE,
                        occurred_at=utc_now(),
                    )
                )

                created = self.names.get(name.value)

                if created is None:
                    raise MonikerReadWriteError(
                        f"Name [{name.value}] could not be read after creation."
                    )

                if name.tags:
                    created = self.names.add_tags(
                        created,
                        name.tags,
                    )

                for source in name.sources:
                    created = self.names.add_source(
                        created,
                        source,
                    )

                return created

        except IntegrityError as error:
            raise NameAlreadyExistsError(
                f"Name already exists: {name.value}"
            ) from error

    def find_names(
        self,
        query: str,
    ) -> tuple[Name, ...]:
        """Find names containing a partial value."""
        return self.names.find(query)

    def list_tags(
        self,
        *,
        name: str | None = None,
        source_title: str | None = None,
        source_type: str | None = None,
        enabled: bool | None = True,
        state: NameState | None = None,
    ) -> tuple[str, ...]:
        """List tags associated with matching names."""
        return self.names.list_tags(
            name=name,
            source_title=source_title,
            source_type=source_type,
            enabled=enabled,
            state=state,
        )

    def name_history(
        self,
        name: str,
    ) -> tuple[NameEvent, ...]:
        """Return a name's lifecycle history."""
        self._current_name(name)

        return self.events.history(name)

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

    def allocate_name(
        self,
        name: str,
        assigned_to: str,
    ) -> NameEvent:
        """Allocate an available name."""
        current = self._current_name(name)

        if not current.enabled or current.state != NameState.AVAILABLE:
            raise InvalidNameTransitionError(
                f"Name [{name}] is not available."
            )

        event = NameEvent(
            name=name,
            assigned_to=assigned_to,
            event=NameEventType.ALLOCATED,
            state=NameState.ALLOCATED,
            occurred_at=utc_now(),
        )

        with self.connection:
            return self.events.append(event)

    def reserve_name(
        self,
        name: str,
        assigned_to: str,
    ) -> NameEvent:
        """Reserve an available name."""
        current = self._current_name(name)

        if not current.enabled or current.state != NameState.AVAILABLE:
            raise InvalidNameTransitionError(
                f"Name [{name}] is not available."
            )

        event = NameEvent(
            name=name,
            assigned_to=assigned_to,
            event=NameEventType.RESERVED,
            state=NameState.RESERVED,
            occurred_at=utc_now(),
        )

        with self.connection:
            return self.events.append(event)


    def release_name(
        self,
        name: str,
    ) -> NameEvent:
        """Release an allocated or reserved name."""
        current = self._current_name(name)

        if current.state == NameState.AVAILABLE:
            raise InvalidNameTransitionError(
                f"Name [{name}] is already available."
            )

        event = NameEvent(
            name=name,
            event=NameEventType.RELEASED,
            state=NameState.AVAILABLE,
            occurred_at=utc_now(),
        )

        with self.connection:
            return self.events.append(event)
