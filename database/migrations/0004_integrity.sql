-- Additive integrity constraints; original sources/events are never rewritten.
DO $$ BEGIN
 IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='local_policy_central_disabled') THEN
  ALTER TABLE local_policy ADD CONSTRAINT local_policy_central_disabled CHECK (jsonb_typeof(central_config)='object' AND (central_config->'enabled') IS NOT DISTINCT FROM 'false'::jsonb);
 END IF;
 IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='audit_hash_shape') THEN
  ALTER TABLE audit_events ADD CONSTRAINT audit_hash_shape CHECK (sha256 ~ '^[0-9a-f]{64}$' AND previous_sha256 ~ '^[0-9a-f]{64}$');
 END IF;
 IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='audit_hash_unique') THEN
  ALTER TABLE audit_events ADD CONSTRAINT audit_hash_unique UNIQUE(sha256);
 END IF;
 IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='chunk_span_binding') THEN
  ALTER TABLE chunks ADD CONSTRAINT chunk_span_binding FOREIGN KEY(document_id,locator) REFERENCES source_spans(document_id,locator);
 END IF;
 IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='chunk_hash_shape') THEN
  ALTER TABLE chunks ADD CONSTRAINT chunk_hash_shape CHECK (sha256 ~ '^[0-9a-f]{64}$');
 END IF;
 IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='verified_reviewer_required') THEN
  ALTER TABLE claims ADD CONSTRAINT verified_reviewer_required CHECK (status<>'verified' OR length(trim(reviewed_by))>0 AND reviewed_by IS NOT NULL);
 END IF;
END $$;
CREATE INDEX IF NOT EXISTS session_messages_scope_time ON session_messages(session_id,id DESC);
CREATE INDEX IF NOT EXISTS inference_runs_day_state ON inference_runs(created_at,state);
CREATE INDEX IF NOT EXISTS learning_proposals_author_state_time ON learning_proposals(author,state,created_at DESC);
CREATE INDEX IF NOT EXISTS claims_active_group ON claims(subject,predicate,status);
