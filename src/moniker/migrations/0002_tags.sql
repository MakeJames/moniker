BEGIN IMMEDIATE;

CREATE TABLE tags (
    name TEXT NOT NULL,
    tag TEXT NOT NULL,

    PRIMARY KEY (name, tag),

    FOREIGN KEY (name)
        REFERENCES names(name)
        ON DELETE CASCADE
);

CREATE INDEX tags_by_tag
ON tags(tag);

PRAGMA user_version = 2;

COMMIT;
