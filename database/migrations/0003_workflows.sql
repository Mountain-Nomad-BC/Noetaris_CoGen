ALTER TABLE documents ADD COLUMN IF NOT EXISTS source_bytes BYTEA;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS original_sha256 TEXT;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS media_type TEXT NOT NULL DEFAULT 'text/plain';
ALTER TABLE documents ADD COLUMN IF NOT EXISTS manifest JSONB NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS ingested_by TEXT NOT NULL DEFAULT 'local-operator';
ALTER TABLE claims ADD COLUMN IF NOT EXISTS revision INTEGER NOT NULL DEFAULT 1;
ALTER TABLE claims ADD COLUMN IF NOT EXISTS reviewed_by TEXT;
CREATE TABLE IF NOT EXISTS source_spans (
 document_id TEXT NOT NULL REFERENCES documents(id), locator TEXT NOT NULL, text TEXT NOT NULL,
 PRIMARY KEY(document_id,locator)
);
CREATE TABLE IF NOT EXISTS chunks (
 id TEXT PRIMARY KEY, document_id TEXT NOT NULL REFERENCES documents(id), locator TEXT NOT NULL,
 text TEXT NOT NULL, sha256 TEXT NOT NULL,
 search TSVECTOR GENERATED ALWAYS AS (to_tsvector('english',text)) STORED
);
CREATE INDEX IF NOT EXISTS chunks_search ON chunks USING GIN(search);
CREATE TABLE IF NOT EXISTS audit_events (
 id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, actor TEXT NOT NULL, event_type TEXT NOT NULL,
 details JSONB NOT NULL, previous_sha256 TEXT NOT NULL, sha256 TEXT NOT NULL,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS sessions (
 id TEXT PRIMARY KEY, owner TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS session_messages (
 id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id),
 role TEXT NOT NULL CHECK(role IN ('user','assistant')), text TEXT NOT NULL, receipt JSONB NOT NULL,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS learning_proposals (
 id TEXT PRIMARY KEY, author TEXT NOT NULL, source_claim_id TEXT NOT NULL REFERENCES claims(id),
 reflection TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'candidate' CHECK(state IN ('candidate','reviewed','rejected')),
 revision INTEGER NOT NULL DEFAULT 1, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS local_policy (
 id INTEGER PRIMARY KEY CHECK(id=1), revision INTEGER NOT NULL DEFAULT 1,
 inference_enabled BOOLEAN NOT NULL DEFAULT true,
 daily_call_limit INTEGER NOT NULL DEFAULT 100 CHECK(daily_call_limit BETWEEN 1 AND 1000),
 max_output_tokens INTEGER NOT NULL DEFAULT 256 CHECK(max_output_tokens BETWEEN 32 AND 512),
 central_config JSONB NOT NULL DEFAULT '{"enabled":false,"provider":"none","issuer":null}'::jsonb
);
INSERT INTO local_policy(id) VALUES(1) ON CONFLICT DO NOTHING;
CREATE TABLE IF NOT EXISTS inference_runs (
 id TEXT PRIMARY KEY, actor TEXT NOT NULL, state TEXT NOT NULL CHECK(state IN ('reserved','completed','failed')),
 details JSONB NOT NULL DEFAULT '{}'::jsonb, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- Immutable evidence and audit protection at DB layer, including against accidental admin SQL.
CREATE OR REPLACE FUNCTION reject_evidence_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
 BEGIN RAISE EXCEPTION 'Immutable evidence: mutation prohibited'; END; $$;
DO $$ BEGIN
 IF NOT EXISTS(SELECT 1 FROM pg_trigger WHERE tgname='audit_immutable') THEN
  CREATE TRIGGER audit_immutable BEFORE UPDATE OR DELETE ON audit_events FOR EACH ROW EXECUTE FUNCTION reject_evidence_mutation();
 END IF;
 IF NOT EXISTS(SELECT 1 FROM pg_trigger WHERE tgname='documents_immutable') THEN
  CREATE TRIGGER documents_immutable BEFORE UPDATE OR DELETE ON documents FOR EACH ROW EXECUTE FUNCTION reject_evidence_mutation();
 END IF;
 IF NOT EXISTS(SELECT 1 FROM pg_trigger WHERE tgname='spans_immutable') THEN
  CREATE TRIGGER spans_immutable BEFORE UPDATE OR DELETE ON source_spans FOR EACH ROW EXECUTE FUNCTION reject_evidence_mutation();
 END IF;
 IF NOT EXISTS(SELECT 1 FROM pg_trigger WHERE tgname='chunks_immutable') THEN
  CREATE TRIGGER chunks_immutable BEFORE UPDATE OR DELETE ON chunks FOR EACH ROW EXECUTE FUNCTION reject_evidence_mutation();
 END IF;
 IF NOT EXISTS(SELECT 1 FROM pg_trigger WHERE tgname='claim_events_immutable') THEN
  CREATE TRIGGER claim_events_immutable BEFORE UPDATE OR DELETE ON claim_events FOR EACH ROW EXECUTE FUNCTION reject_evidence_mutation();
 END IF;
END; $$;
