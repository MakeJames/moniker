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

The application listens on 127.0.0.1:8042 by default.
Nginx provides the HTTP-facing entry point.

### Configuration

Deployment defaults are defined in:

```
deploy/defaults.mk
```

Machine-specific overrides can be placed in:

```
deploy/local.mk
```

`deploy/local.mk` is ignored by Git.

**For example:**

```
MONIKER_PORT = 8123
MONIKER_SERVER_NAME = moniker.example.test
MONIKER_LOG_LEVEL = warning
```

Individual values can also be overridden when invoking Make:

```
make configure MONIKER_PORT=8123
```

To inspect the effective configuration:

```
make show-config
```

### Generate deployment files

Generate the systemd, Nginx and environment files with:

```
make configure
```

The rendered files are written to:

```
build/deploy/
```

They can be inspected before anything is installed on the host.

### Initial installation

A fresh deployment can be performed as a series of explicit steps:

```
make install
make install-config
make migrate
make enable
```

Each command has a separate responsibility.

#### `make install`

Build and install the Moniker application.

This:

- creates the moniker service user and group when required
- builds a Python wheel
- creates the application virtual environment
- installs Moniker under /opt/moniker
- creates /var/lib/moniker for persistent state

Application code is installed as root-owned files.
The moniker service account owns only the persistent state it needs to
modify.

#### `make install-config`

Install the generated host configuration.

This installs:

```
/etc/moniker/moniker.env
/etc/systemd/system/moniker.service
/etc/nginx/sites-available/moniker
```

The generated files can be reviewed first with:

```
make configure
make migrate
```

Bring the Moniker database schema up to the version required by the installed
application:

```
make migrate
```

The migration runs as the moniker service account and uses the configured
database location.

By default this is: `/var/lib/moniker/moniker.db`

#### `make enable`

Enable the installed service: `make enable`

This:

- reloads the systemd configuration
- enables the Moniker Nginx site
- validates the Nginx configuration
- enables and starts moniker.service
- reloads Nginx

Nginx configuration is validated before it is reloaded.

#### Complete deployment

Where inspection of each individual stage is not required, the complete
initial deployment can be run with:

```
make deploy
```

This performs the installation sequence in order:

```
install
    ↓
install-config
    ↓
migrate
    ↓
enable
```

#### Upgrading Moniker

Application upgrades do not normally need to reinstall the host
configuration.

Upgrade the application with: `make upgrade`

This:

```
installs the new application
    ↓
runs database migrations
    ↓
restarts Moniker
```

Configuration changes can be installed separately with: `make install-config`

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
