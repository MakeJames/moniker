"""The classes and methods of the NameStore."""

from collections.abc import Sequence
from sqlite3 import Connection, Row

from moniker.domain import Name, NameState, Source
from moniker.stores.errors import MonikerReadWriteError


class NameStore:
    """Persist and retrieve names from Moniker's catalogue.

    This store owns persistence operations for catalogue names
    and the relationships that attach names to other catalogue data.

    - creating and retrieving names
    - managing and updating name metadata
    - managing tags
    - constructing `Name` domain objects

    Attributes:
        connection:
            An active connection to the Database.

    Methods:
        list:
            List all names matching the supplied filters.

        get:
            Get a single record from the name catalogue.

    """

    def __init__(self, connection: Connection) -> None:
        """Instantiate the class."""
        self.connection = connection

    def list(
        self,
        *,
        tags: tuple[str, ...] = (),
        source_title: str | None = None,
        source_type: str | None = None,
        enabled: bool | None = True,
        state: NameState | None = None,
    ) -> tuple[Name, ...]:
        """List names in the catalogue.

        Fetch and filter lists of names in the catalogue.
        Run multi-part queries to find and subset the dataset.
        This includes filtering by tag,
        source title or genre,
        and availability.

        Attributes:
            tags:
                String Tuple of tags such as `("fantasy", "networking")`.

            source_title:
                Name of a given source material.

            source_type:
                The type or genre of number of sources.

            enabled:
                Whether the name is currently active.

            state:
                The availability of the name.

        """
        query, params = self._build_query(
            tags=tags,
            source_title=source_title,
            source_type=source_type,
            enabled=enabled,
            state=state,
        )
        query = query + "\norder by names.name"
        results = self.connection.execute(query, params).fetchall()
        return self._hydrate_names(results)

    def get(self, name: str) -> Name | None:
        """Fetch a catalogue item from its name.

        Returns a single entry from the catalogue if it is there.

        For speculative name queries use the list

        Attributes:
            name:
                A string identifier for the catalogue item.

        """
        self._validate_query_value(name, "name")

        query = """
            select
                names.name,
                names.description,
                names.enabled,
                current_event.state
            from names
            join name_events as current_event
              on current_event.name = names.name
             and current_event.occurred_at = (
                    select max(history.occurred_at)
                    from name_events as history
                    where history.name = names.name
                )
           where names.name = ?
        """
        result = self.connection.execute(query, (name,)).fetchall()
        if result == []:
            return None

        return self._hydrate_names(result)[0]

    def find(self, search_query: str) -> tuple[Name, ...]:
        """Find catalogue names matching a partial value."""
        self._validate_query_value(search_query, "query")

        _search_query = self._escape_like(search_query)

        query = """
            select
                names.name,
                names.description,
                names.enabled,
                current_event.state
            from names
            join name_events as current_event
              on current_event.name = names.name
             and current_event.occurred_at = (
                    select max(history.occurred_at)
                    from name_events as history
                    where history.name = names.name
                )
            where names.name like ? escape '!' collate nocase
            order by names.name
        """

        rows = self.connection.execute(
            query, (f"%{_search_query}%",)
        ).fetchall()

        return self._hydrate_names(rows)

    def create(self, name: Name) -> Name:
        """Create a catalogue name.

        This method only creates the name.
        Further persistence orchestration is required to map source,
        event (such as created),
        and tag metadata.

        Attributes:
            name:
                The name to be created.

        """
        query = """
            insert into names (
                name,
                description,
                enabled
            ) values (?, ?, ?)
        """

        self.connection.execute(
            query, (name.value, name.description, name.enabled)
        )

        return name

    def add_tags(self, name: Name, tags: tuple[str, ...]) -> Name:
        """Associate a name with tags.

        Attributes:
            name:
                A name object as currently represented in the database
            tags:
                A set of tags to be applied to the given name

        """
        params: list[tuple[str, ...]] = []
        self._validate_query_value(name.value, "name")
        unique_tags = tuple(dict.fromkeys(tags))

        for tag in unique_tags:
            self._validate_query_value(tag, "tag")
            if tag in name.tags:
                continue
            params.append((name.value, tag))

        query = "insert into tags (name, tag) values (?, ?)"

        self.connection.executemany(query, params)

        updated_name = self.get(name.value)

        if updated_name is None:
            raise MonikerReadWriteError(f"Name [{name.value}] not found.")

        return updated_name

    def list_tags(
        self,
        *,
        name: str | None = None,
        source_title: str | None = None,
        source_type: str | None = None,
        enabled: bool | None = True,
        state: NameState | None = None,
    ) -> tuple[str, ...]:
        """List tags in the catalogue.

        Fetch and filter lists of tags in the catalogue.
        Run multi-part queries to find and subset the dataset.
        This includes filtering by name,
        source title or genre,
        and availability.

        Attributes:
            name:
                A catalogue name item.

            source_title:
                Name of a given source material.

            source_type:
                The type or genre of number of sources.

            enabled:
                Whether the name is currently active.

            state:
                The availability of the name associated with the tag.

        """
        query = """
            select distinct
                tags.tag
            from tags
            join names
              on names.name = tags.name
            join name_events as current_event
              on current_event.name = names.name
             and current_event.occurred_at = (
                    select max(history.occurred_at)
                    from name_events as history
                    where history.name = names.name
             )
        """

        filters, params = self._build_filters(
            name=name,
            source_title=source_title,
            source_type=source_type,
            enabled=enabled,
            state=state,
        )

        query += filters
        query += """\norder by tags.tag"""

        rows = self.connection.execute(query, params).fetchall()
        return tuple(row["tag"] for row in rows)

    def add_source(self, name: Name, source: Source) -> Name:
        """Associate a name with a source.

        Names can have multiple sources.
        This method allows a user to extend a name to additional sources,
        to provide further context and meaning.

        Returns a new Name object with all sources.

        Attributes:
            name:
                A name object.
            source:
                A source object to be associated with the catalogue entry.

        """
        query = """
            insert into name_sources(
                name,
                source_title,
                source_type
            )
            values (?, ?, ?)
        """

        self.connection.execute(
            query,
            (
                name.value,
                source.title,
                source.type,
            ),
        )

        created_name = self.get(name.value)

        if created_name is None:
            raise MonikerReadWriteError(
                f"Created name [{name.value}] could not be found.",
            )

        return created_name

    def pick(
        self,
        *,
        tags: tuple[str, ...] = (),
        source_title: str | None = None,
        source_type: str | None = None,
        enabled: bool = True,
        state: NameState | None = NameState.AVAILABLE,
    ) -> Name | None:
        """Pick a name from the catalogue.

        Fetch a random entry from the catalogue.
        Run multi-part filters to subset the dataset including:
        filtering by tag,
        source title or genre,
        and availability.

        Attributes:
            tags:
                String Tuple of tags such as `("fantasy", "networking")`.

            source_title:
                Name of a given source material.

            source_type:
                The type or genre of number of sources.

            enabled:
                Whether the name is currently active (default: True).

            state:
                The availability of the name (default: available).

        """
        query, params = self._build_query(
            tags=tags,
            source_title=source_title,
            source_type=source_type,
            enabled=enabled,
            state=state,
        )
        query = (
            query
            + """
            order by random()
            limit 1
        """
        )
        result = self.connection.execute(query, params).fetchone()
        name = self._hydrate_names((result,))

        if name == ():
            return None

        return name[0]

    def _build_filters(
        self,
        *,
        name: str | None = None,
        tags: tuple[str, ...] = (),
        source_title: str | None = None,
        source_type: str | None = None,
        enabled: bool | None = True,
        state: NameState | None = None,
    ) -> tuple[str, tuple[str | int, ...]]:
        """Construct query filters."""
        self._validate_query_value(name, "name")
        self._validate_query_value(source_title, "source_title")
        self._validate_query_value(source_type, "source_type")
        unique_tags = tuple(dict.fromkeys(tags))

        for tag in unique_tags:
            self._validate_query_value(tag, "tag")

        source_filters: list[str] = []
        filters: list[str] = []
        params: list[str | int] = []

        if name is not None:
            filters.append("names.name = ?")
            params.append(name)

        for tag in unique_tags:
            filters.append(
                """
                exists (
                    select 1
                    from tags as filter_tags
                    where filter_tags.name = names.name
                      and filter_tags.tag = ?

                )
                """
            )
            params.append(tag)

        if enabled is not None:
            filters.append("names.enabled = ?")
            params.append(int(enabled))

        if state is not None:
            filters.append("current_event.state = ?")
            params.append(state.value)

        if source_title is not None:
            source_filters.append("name_sources.source_title = ?")
            params.append(source_title)

        if source_type is not None:
            source_filters.append("name_sources.source_type = ?")
            params.append(source_type)

        if source_title is not None or source_type is not None:
            source_filters.append("name_sources.name = names.name")

            source_filter: tuple[str, ...] = (
                """
                exists (
                    select 1
                    from name_sources
                    where
                """,
                "        and ".join(source_filters),
                """
                )
                """,
            )

            filters.append("".join(source_filter))

        if not filters:
            return "", tuple(params)

        return (
            " where " + " and ".join(filters),
            tuple(params),
        )

    def _build_query(
        self,
        *,
        tags: tuple[str, ...] = (),
        source_title: str | None = None,
        source_type: str | None = None,
        enabled: bool | None = True,
        state: NameState | None = None,
    ) -> tuple[str, tuple[str | int, ...]]:
        """Build a query for filtering catalogue names."""
        query = """
            select
                names.name,
                names.description,
                names.enabled,
                current_event.state
            from names
            join name_events as current_event
              on current_event.name = names.name
             and current_event.occurred_at = (
                    select max(history.occurred_at)
                    from name_events as history
                    where history.name = names.name
                )
        """

        filters, params = self._build_filters(
            tags=tags,
            source_title=source_title,
            source_type=source_type,
            enabled=enabled,
            state=state,
        )

        return query + filters, params

    def _hydrate_names(
        self,
        rows: Sequence[Row],
    ) -> tuple[Name, ...]:
        """Construct complete Name objects from catalogue rows."""
        if not rows:
            return ()

        names = tuple(row["name"] for row in rows if row is not None)

        if names == ():
            return ()

        placeholders = ", ".join("?" for _ in names)

        # ruff: ignore[S608]
        # Placeholder query is constructed avoiding direct user input
        tag_query = f"""
            select
                name,
                tag
            from tags
            where name in ({placeholders})
            order by name, tag
            """

        # ruff: ignore[S608]
        # Placeholder query is constructed avoiding direct user input
        source_query = f"""
            select
                name_sources.name,
                sources.title,
                sources.description,
                sources.type
            from name_sources
            join sources
              on sources.title = name_sources.source_title
             and sources.type = name_sources.source_type
            where name_sources.name in ({placeholders})
            order by
                name_sources.name,
                sources.title,
                sources.type
            """

        tag_rows = self.connection.execute(tag_query, names).fetchall()

        source_rows = self.connection.execute(source_query, names).fetchall()

        tags_by_name: dict[str, list[str]] = {name: [] for name in names}

        sources_by_name: dict[str, list[Source]] = {name: [] for name in names}

        for row in tag_rows:
            tags_by_name[row["name"]].append(row["tag"])

        for row in source_rows:
            sources_by_name[row["name"]].append(
                Source(
                    title=row["title"],
                    description=row["description"],
                    type=row["type"],
                )
            )

        return tuple(
            Name(
                value=row["name"],
                description=row["description"],
                enabled=bool(row["enabled"]),
                state=NameState(row["state"]),
                tags=tuple(tags_by_name[row["name"]]),
                sources=tuple(sources_by_name[row["name"]]),
            )
            for row in rows
        )

    @staticmethod
    def _validate_query_value(
        value: str | None,
        field: str,
    ) -> None:
        if value is not None and not value.strip():
            raise ValueError(f"{field} must not be empty")

    @staticmethod
    def _escape_like(value: str) -> str:
        """Escape characters with special meaning in SQLite LIKE patterns."""
        return value.replace("!", "!!").replace("%", "!%").replace("_", "!_")
