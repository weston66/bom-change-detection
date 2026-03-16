CREATE TABLE IF NOT EXISTS bom_audit_log (
    id            SERIAL PRIMARY KEY,
    bom_id        VARCHAR NOT NULL,
    change_type   VARCHAR NOT NULL,  -- ADDED, REMOVED, MODIFIED
    old_value     TEXT,
    new_value     TEXT,
    detected_at   TIMESTAMP NOT NULL
);
