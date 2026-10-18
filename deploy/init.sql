CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    source_version TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(sha256, source_version)
);
CREATE TABLE IF NOT EXISTS claims (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE RESTRICT,
    subject TEXT NOT NULL,
    predicate TEXT NOT NULL,
    value TEXT NOT NULL,
    locator TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'candidate' CHECK(status IN ('candidate', 'verified', 'contested', 'rejected', 'superseded')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS claims_lookup ON claims(subject, predicate);
CREATE TABLE IF NOT EXISTS claim_events (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    claim_id TEXT NOT NULL REFERENCES claims(id) ON DELETE RESTRICT,
    event_type TEXT NOT NULL,
    actor TEXT NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- No UPDATE/DELETE endpoints for evidence or claim events in the starter.
-- For production, enforce append-only at the database privilege/trigger layer.
