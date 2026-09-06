BEGIN IMMEDIATE;

CREATE TABLE names (
    name TEXT PRIMARY KEY,
    source TEXT,
    description TEXT,
    enabled INTEGER NOT NULL DEFAULT 1
        CHECK (enabled IN (0, 1)),
    created_at TEXT NOT NULL
);

CREATE TABLE allocations (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    assigned_to TEXT NOT NULL,
    assigned_at TEXT NOT NULL,
    released_at TEXT,

    FOREIGN KEY (name)
        REFERENCES names(name)
);

CREATE UNIQUE INDEX one_active_allocation_per_name
ON allocations(name)
WHERE released_at IS NULL;

CREATE UNIQUE INDEX one_active_name_per_device
ON allocations(assigned_to)
WHERE released_at IS NULL;

PRAGMA user_version = 1;

COMMIT;
