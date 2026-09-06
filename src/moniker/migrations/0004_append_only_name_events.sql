BEGIN IMMEDIATE;

CREATE TRIGGER name_events_prevent_update
BEFORE UPDATE ON name_events
BEGIN
    SELECT RAISE(
        ABORT,
        'name_events is append-only'
    );
END;

CREATE TRIGGER name_events_prevent_delete
BEFORE DELETE ON name_events
BEGIN
    SELECT RAISE(
        ABORT,
        'name_events is append-only'
    );
END;

PRAGMA user_version = 4;

COMMIT;
