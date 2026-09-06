# Moniker

A helpful naming api to support the home-lab-ing sysadmin.

Moniker is a small API for discovering,
curating and suggesting names to devices and services.

Manage name allocation.
Create new names.
Get a name for new service.
Simple.

Moniker serves one very simple problem:
naming something is about the hardest thing that you can do!

Create a catalogue of names,
their sources and useful characteristics,
and request one when you're next struggling to come up with a name.

## Status

Moniker us currently under active development.

## Requirements

- Python 3.14
- `uv`
- SQLite

## Installation

Clone the repository and install the project dependencies:

```sh
git clone https://github.com/MakeJames/moniker.git
cd moniker
uv sync
```

Run the development server with

```sh
uv run uvicorn moniker.app:app --reload
```

The API will normally be available at `http://127.0.0.1:8000/`

### Database

Moniker stores its persistent state in SQLite.

By default the database is created at: `data/moniker.db`

The location can be overridden with the `MONIKER_DATABASE` environment variable:

```sh
export MONIKER_DATABASE=/var/lib/moniker/moniker.db
```

## Architecture

Moniker keeps its major concerns deliberately separate.

- domain
    - describes names, sources and lifecycle events
- persistence
    - stores and retrieves domain objects using SQLite
- response
    - describes HTTP representations and links
- application
    - exposes those resources through FastAPI

Moniker intentionally avoids an ORM at this stage.

The database model is small,
the SQL is useful documentation,
and explicit queries make the persistence behaviour easier to understand and recover.

## Testing

Run the test suite with:

```sh
uv run pytest
```

Run Ruff with:

```sh
uv run ruff check
```

## Code quality

The project uses:

- Ruff: formatting and linting
- mypy: type checking

## Contributing

Moniker is currently a small home-lab project,
but development follows the same expectations as a larger service:

- make the smallest useful change
- add or update tests
- run the full test suite
- run static checks
- document architectural decisions when they change

Useful commands include:

```sh
uv sync
uv run pytest
uv run ruff
uv run moniker-migrate
```
