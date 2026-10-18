CREATE TABLE IF NOT EXISTS governed_records (
 id TEXT PRIMARY KEY CHECK(id ~ '^[0-9a-f]{64}$'),
 kind TEXT NOT NULL CHECK(kind IN ('assembly','issues','proposal','extraction')),
 author TEXT NOT NULL,
 document_id TEXT REFERENCES documents(id),
 source_sha256 TEXT NOT NULL CHECK(source_sha256 ~ '^[0-9a-f]{64}$'),
 payload JSONB NOT NULL,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS governed_reviews (
 id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 record_id TEXT NOT NULL REFERENCES governed_records(id),
 actor TEXT NOT NULL CHECK(length(trim(actor))>0),
 decision TEXT NOT NULL CHECK(decision IN ('reviewed','rejected')),
 rationale TEXT NOT NULL CHECK(length(rationale)>=10),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 UNIQUE(record_id)
);
CREATE TABLE IF NOT EXISTS policy_actions (
 id TEXT PRIMARY KEY CHECK(id ~ '^[0-9a-f]{64}$'),
 requested_by TEXT NOT NULL,
 policy_revision INTEGER NOT NULL CHECK(policy_revision>0),
 payload JSONB NOT NULL,
 state TEXT NOT NULL CHECK(state IN ('pending','applied','rejected')),
 approved_by TEXT,
 expires_at TIMESTAMPTZ NOT NULL,
 receipt_sha256 TEXT,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS invocation_receipts (
 actor TEXT NOT NULL,
 request_id TEXT NOT NULL CHECK(request_id ~ '^[0-9a-f]{32}$'),
 payload_sha256 TEXT NOT NULL CHECK(payload_sha256 ~ '^[0-9a-f]{64}$'),
 state TEXT NOT NULL CHECK(state IN ('pending','completed','failed')),
 response JSONB,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 PRIMARY KEY(actor,request_id)
);
CREATE INDEX IF NOT EXISTS governed_records_scope_time ON governed_records(document_id,kind,created_at DESC);
CREATE INDEX IF NOT EXISTS policy_actions_state_expiry ON policy_actions(state,expires_at);
DO $$ DECLARE entry TEXT; BEGIN
 FOREACH entry IN ARRAY ARRAY['governed_records','governed_reviews'] LOOP
  IF NOT EXISTS(SELECT 1 FROM pg_trigger WHERE tgname=entry||'_immutable') THEN
   EXECUTE format('CREATE TRIGGER %I BEFORE UPDATE OR DELETE ON %I FOR EACH ROW EXECUTE FUNCTION reject_evidence_mutation()',entry||'_immutable',entry);
  END IF;
 END LOOP;
END $$;
DO $$ BEGIN
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='nsai_app') THEN
  GRANT SELECT,INSERT ON governed_records,governed_reviews,policy_actions,invocation_receipts TO nsai_app;
  GRANT UPDATE(state,approved_by,receipt_sha256) ON policy_actions TO nsai_app;
  GRANT UPDATE(state,response) ON invocation_receipts TO nsai_app;
  GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO nsai_app;
 END IF;
END $$;
