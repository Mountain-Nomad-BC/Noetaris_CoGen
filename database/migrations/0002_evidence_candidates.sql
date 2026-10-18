-- TARGET migration draft / NOT APPLIED / staging-test before deploy.
-- Additive schema for source revisions, assertions, links, audit and index history.
-- Does not migrate old documents/claims; write and test separate backfill job.
CREATE TABLE IF NOT EXISTS source_revisions (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  source_key TEXT NOT NULL,
  revision TEXT NOT NULL,
  content_sha256 CHAR(64) NOT NULL CHECK(content_sha256 ~ '^[a-f0-9]{64}$'),
  media_type TEXT NOT NULL,
  bytes_size BIGINT NOT NULL CHECK(bytes_size >= 0),
  observed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (project_id, source_key, revision, content_sha256)
);
CREATE TABLE IF NOT EXISTS claim_assertions (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  source_revision_id TEXT NOT NULL REFERENCES source_revisions(id) ON DELETE RESTRICT,
  subject TEXT NOT NULL,
  predicate TEXT NOT NULL,
  value_text TEXT NOT NULL,
  locator TEXT NOT NULL,
  observed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  valid_from TIMESTAMPTZ NULL,
  valid_until TIMESTAMPTZ NULL,
  CHECK(valid_until IS NULL OR valid_from IS NULL OR valid_until > valid_from)
);
CREATE INDEX IF NOT EXISTS claim_assertions_topic ON claim_assertions(project_id, subject, predicate);
CREATE TABLE IF NOT EXISTS claim_relations (
  relation_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  left_assertion_id TEXT NOT NULL REFERENCES claim_assertions(id),
  right_assertion_id TEXT NOT NULL REFERENCES claim_assertions(id),
  relation_type TEXT NOT NULL CHECK(relation_type IN ('supports','contradicts','duplicates','supersedes')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (left_assertion_id <> right_assertion_id)
);
CREATE TABLE IF NOT EXISTS claim_decisions (
  decision_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  assertion_id TEXT NOT NULL REFERENCES claim_assertions(id),
  actor_id TEXT NOT NULL,
  decision TEXT NOT NULL CHECK(decision IN ('verified','contested','rejected','superseded')),
  evidence_receipt_sha256 CHAR(64) NOT NULL CHECK(evidence_receipt_sha256 ~ '^[a-f0-9]{64}$'),
  recorded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS index_generations (
  generation_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  source_set_sha256 CHAR(64) NOT NULL,
  embedder_id TEXT NOT NULL,
  index_sha256 CHAR(64) NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('building','candidate','validated','active','rejected','rolled_back')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- These append-only triggers prevent accidental update/delete for non-superusers.
-- Superusers/owners can still bypass/drop trigger; immutable signed external anchoring is future work.
CREATE OR REPLACE FUNCTION nsai_refuse_update_delete() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'NSAI evidence records are append-only';
END $$;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'nsai_assertions_immutable') THEN
    CREATE TRIGGER nsai_assertions_immutable BEFORE UPDATE OR DELETE ON claim_assertions
      FOR EACH ROW EXECUTE FUNCTION nsai_refuse_update_delete();
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'nsai_decisions_immutable') THEN
    CREATE TRIGGER nsai_decisions_immutable BEFORE UPDATE OR DELETE ON claim_decisions
      FOR EACH ROW EXECUTE FUNCTION nsai_refuse_update_delete();
  END IF;
END $$;
-- Production TODO: authorization policy on each project id; enforce cross-table project matches,
-- separate writer/migration roles and tenant RLS; signed decision verification before INSERT;
-- active index transition through event table rather than unrestricted status UPDATE.
