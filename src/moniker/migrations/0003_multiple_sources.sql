PRAGMA foreign_keys = OFF;

BEGIN IMMEDIATE;


/* New Names Table */

CREATE TABLE names_new (
    name TEXT PRIMARY KEY,
    description TEXT,
    enabled INTEGER NOT NULL DEFAULT 1
        CHECK (enabled IN (0, 1))
);

INSERT INTO names_new (
    name,
    description,
    enabled
)
SELECT
    name,
    description,
    enabled
FROM names;

/* New Sources Tables */

CREATE TABLE sources (
    title TEXT NOT NULL,
    description TEXT,
    type TEXT NOT NULL,

    PRIMARY KEY (
        title,
        type
    )
);

CREATE TABLE name_sources (
    name TEXT NOT NULL,
    source_title TEXT NOT NULL,
    source_type TEXT NOT NULL,

    PRIMARY KEY (
        name,
        source_title,
        source_type
    ),

    FOREIGN KEY (name)
        REFERENCES names_new(name)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    FOREIGN KEY (
        source_title,
        source_type
    )
        REFERENCES sources(
            title,
            type
        )
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

INSERT INTO sources (
    title,
    type
)
SELECT DISTINCT
    source,
    'unknown'
FROM names
WHERE source IS NOT NULL
    AND TRIM(source) != '';

INSERT INTO name_sources (
    name,
    source_title,
    source_type
)
SELECT
    name,
    source,
    'unknown'
FROM names
WHERE source IS NOT NULL
  AND TRIM(source) != '';

CREATE INDEX name_sources_by_source
ON name_sources (
    source_title,
    source_type,
    name
);

CREATE INDEX sources_by_type
ON sources (
    type,
    title
);

/* New name_events table */

CREATE TABLE name_events (
    name TEXT NOT NULL,
    assigned_to TEXT,
    event TEXT NOT NULL,
    state TEXT NOT NULL,
    occurred_at TEXT NOT NULL,

    PRIMARY KEY (
        name,
        occurred_at
    ),

    FOREIGN KEY (name)
        REFERENCES names_new(name)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CHECK (
           (event = 'created'    AND state = 'available')
        OR (event = 'allocated'  AND state = 'allocated')
        OR (event = 'reserved'   AND state = 'reserved')
        OR (event = 'released'   AND state = 'available')
    )
);

INSERT INTO name_events (
    name,
    assigned_to,
    event,
    state,
    occurred_at
)
SELECT
    name,
    NULL,
    'created',
    'available',
    created_at
FROM names;

INSERT INTO name_events (
    name,
    assigned_to,
    event,
    state,
    occurred_at
)
SELECT
    name,
    assigned_to,
    'allocated',
    'allocated',
    assigned_at
FROM allocations;

INSERT INTO name_events (
    name,
    assigned_to,
    event,
    state,
    occurred_at
)
SELECT
    name,
    assigned_to,
    'released',
    'available',
    released_at
FROM allocations
WHERE released_at IS NOT NULL;

CREATE INDEX name_events_latest
ON name_events (
    name,
    occurred_at DESC
);

/* Clean up */

DROP TABLE allocations;
DROP TABLE names;

ALTER TABLE names_new
RENAME TO names;

PRAGMA user_version = 3;

COMMIT;

PRAGMA foreign_keys = ON;
