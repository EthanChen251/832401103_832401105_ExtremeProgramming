PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS contacts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT
                CHECK (id BETWEEN 1 AND 9007199254740991),
    name        TEXT NOT NULL CHECK (
                    typeof(name) = 'text' AND length(name) BETWEEN 1 AND 100
                    AND instr(name, char(10)) = 0 AND instr(name, char(13)) = 0
                ),
    notes       TEXT NOT NULL DEFAULT '' CHECK (typeof(notes) = 'text' AND length(notes) <= 2000),
    favorite    INTEGER NOT NULL DEFAULT 0 CHECK (favorite IN (0, 1)),
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS contact_methods (
    contact_id  INTEGER NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    type        TEXT NOT NULL CHECK (type IN ('phone', 'email', 'social', 'address')),
    position    INTEGER NOT NULL CHECK (typeof(position) = 'integer' AND position BETWEEN 0 AND 19),
    value       TEXT NOT NULL CHECK (
                    typeof(value) = 'text' AND length(value) BETWEEN 1 AND 500
                    AND instr(value, char(10)) = 0 AND instr(value, char(13)) = 0
                ),
    PRIMARY KEY (contact_id, type, position),
    UNIQUE (contact_id, type, value)
);

CREATE INDEX IF NOT EXISTS idx_contacts_favorite_id ON contacts(favorite, id);
