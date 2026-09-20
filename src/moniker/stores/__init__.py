"""Store methods for the Moniker catalogue.

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

from moniker.stores.errors import MonikerReadWriteError
from moniker.stores.event import NameEventStore
from moniker.stores.name import NameStore
from moniker.stores.source import SourceStore


__all__ = [
    "MonikerReadWriteError",
    "NameEventStore",
    "NameStore",
    "SourceStore",
]
