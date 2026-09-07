"""FastAPI dependencies for the Moniker application.

Construct application-layer dependencies used by HTTP routes.

This module is responsible for:

- opening database connections for API requests
- constructing Catalogue instances
- closing database connections after requests complete

It does not:

- execute catalogue operations
- manage catalogue transaction boundaries
- construct API responses

"""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends

from moniker.catalogue import Catalogue
from moniker.database import connect


def get_catalogue() -> Iterator[Catalogue]:
    """Provide a Catalogue for the lifetime of an API request."""
    connection = connect()

    try:
        yield Catalogue(connection)
    finally:
        connection.close()


CatalogueDependency = Annotated[
    Catalogue,
    Depends(get_catalogue),
]
