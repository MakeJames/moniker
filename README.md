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

## Usage

The API is designed to be self discoverable and self linking.
Fastapi serves OpenAPI docs on `/docs`.

The main resources can be found at 

```
/names
/sources
/suggestion
```

### Browse names

List the names in the catalogue: `curl moniker.local/names`.
Filer names by tag, source or availability or search in the catalogue:
`curl moniker.local/names?tag=fruit&tag=orchard&state=available`

### Ask for a suggestion

Request an available name with `curl moniker.local/suggestion`.
Suggestions can be narrowed using tags or sources in the query parameters,
`curl moniker.local/suggestion?source_title=Pond&source_type=Garden`

### Adding names

Create a new entry with:

```
curl \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{
      "value": "dragnfruit",
      "description": "A dramatic fruit.",
      "tags": ["fruit", "tropical"],
      "source": {
        "title": "Fruit Aisle",
        "type": "Supermarket"
      }
    }' \
    "moniker.local/names"
```

#### Add multiple names

At this point there is no separate 'bulk-import API'.
Collections of names can be imported on individual api requests
using other shell utilities such as:

```
tail -n +2 names.csv |
while IFS=, read -r value description tags; do
    jq -n \
        --arg value "$value" \
        --arg description "$description" \
        --arg tags "$tags" \
        '{
            value: $value,
            description: $description,
            tags: ($tags | split(";"))
        }' |
    curl \
        -X POST \
        -H "Content-Type: application/json" \
        -d @- \
        "moniker.local/names"
done
```

## Installation

### Requirements

- Python 3.14
- `make`
- `uv`
- Nginx
- SQLite
- systemd

Moniker is deployed as a bare metal installation.
It does not require a container runtime.

### Development

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

During development, a database is created at: `data/moniker.db`

For the standard host deployment it is: `/var/lib/moniker/moniker.db`

The database location can be overridden with the MONIKER_DATABASE
environment variable or through the deployment configuration.

### Deployment

Moniker can generate and install the files required to run the application
using Uvicorn, systemd and Nginx.

The default deployment layout is:

```
/opt/moniker/
    application virtual environment

/etc/moniker/
    application configuration

/var/lib/moniker/
    SQLite database and persistent state

/etc/systemd/system/
    moniker.service

/etc/nginx/sites-available/
    moniker
```

A more detailed [deployment guide](./docs/deployment.md)
outlines step by step upgrade and first installation paths.

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
