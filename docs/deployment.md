## Usage

Moniker uses `make` as its operator interface.

The Make targets separate application installation,
host configuration,
database migration,
service activation and recovery
so that each step can be inspected and run independently.

### Inspect the configuration

Show the effective deployment configuration with:

```sh
make show-config
```

Deployment defaults are read from `deploy/defaults.mk`.

Machine-specific values can be placed in the ignored
`deploy/local.mk` file:

```makefile
MONIKER_PORT = 8123
MONIKER_SERVER_NAME = moniker.example.test
MONIKER_LOG_LEVEL = warning
```

Values can also be overridden for an individual command:

```sh
make configure MONIKER_PORT=8123
```

Generate the systemd,
Nginx and environment configuration with:

```sh
make configure
```

The rendered files are written to `build/deploy/`
and can be inspected before they are installed.

### First deployment

A complete first deployment can be run with:

```sh
make deploy
```

This performs the following operations in order:

```text
install
    ↓
install-config
    ↓
migrate
    ↓
activate
    ↓
enable
```

The same steps can be run separately:

```sh
make install
make install-config
make migrate
make activate
make enable
```

`make install` builds the current Moniker release
and installs it into a versioned directory beneath:

```text
/opt/moniker/releases/
```

`make activate` updates:

```text
/opt/moniker/current
```

to point at the release that should be served.

Persistent state is kept separately under:

```text
/var/lib/moniker/
```

so application releases can be replaced or rolled back
without moving the database.

### Database migrations

Bring the database schema up to the version required by
the current release with:

```sh
make migrate
```

Before migrating an existing database,
Moniker creates a backup under:

```text
/var/lib/moniker/backups/
```

On a first installation there is no existing database to back up,
so the migration creates the database and applies the schema from scratch.

Migrations are safe to run again when the database is already current.

### Upgrading

After checking out a newer Moniker release,
upgrade the installed application with:

```sh
make upgrade
```

This:

```text
installs the new release
    ↓
backs up and migrates the database
    ↓
activates the new release
```

Host configuration is not normally reinstalled during an application
upgrade.

If deployment configuration has also changed,
install it separately:

```sh
make install-config
```

### Installed versions

Show the application releases currently installed on the host with:

```sh
make list-versions
```

The active release is marked as `current`.

For example:

```text
0.1.0
0.1.1  (current)
```

Old releases are retained so that the application can be rolled back
without rebuilding them.

### Rolling back

Switch back to an installed application release with:

```sh
make rollback RELEASE=0.1.0
```

Rollback changes the active application release
and restarts Moniker.

It does **not** restore the database.

This distinction is deliberate:
an application rollback is relatively safe,
while restoring persistent data can discard changes made since the backup.

### Restoring a database backup

Database restoration is an explicit operation.

Specify the backup to restore:

```sh
make restore \
    BACKUP=/var/lib/moniker/backups/moniker-pre-0.1.1.db
```

Moniker is stopped while the database is replaced
and started again afterwards.

Review the selected backup before running this command.

### Disabling Moniker

Disable the deployed service with:

```sh
make uninstall
```

This:

* stops and disables `moniker.service`
* removes Moniker from Nginx's enabled sites
* validates and reloads Nginx

It deliberately preserves:

```text
/opt/moniker/                 installed releases
/etc/moniker/                 configuration
/var/lib/moniker/             database and backups
/etc/systemd/system/          service definition
/etc/nginx/sites-available/   Nginx configuration
```

`uninstall` does not remove data, or clean up system files.

### Checking the service

Once deployed,
the lightweight health endpoint can be queried with:

```sh
curl http://moniker.local/health
```

The application root provides links to the main API resources:

```sh
curl http://moniker.local/
```

Names can then be listed with:

```sh
curl http://moniker.local/names
```

and an available name requested with:

```sh
curl http://moniker.local/suggestion
```

Filters can be supplied through query parameters:

```sh
curl \
    'http://moniker.local/suggestion?tag=fruit&tag=orchard'
```

