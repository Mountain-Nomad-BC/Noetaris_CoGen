-- Append supplemental extraction generations without rewriting source or previous artifacts.
CREATE TABLE IF NOT EXISTS research_supplements (
 id TEXT PRIMARY KEY CHECK(id ~ '^[0-9a-f]{64}$'),
 document_id TEXT NOT NULL REFERENCES document_knowledge(document_id),
 kind TEXT NOT NULL CHECK(kind IN ('ocr','author_math')),
 source_sha256 TEXT NOT NULL CHECK(source_sha256 ~ '^[0-9a-f]{64}$'),
 review_record_id TEXT NOT NULL REFERENCES governed_records(id),
 payload JSONB NOT NULL CHECK(jsonb_typeof(payload)='object'),
 author TEXT NOT NULL,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS research_supplements_document ON research_supplements(document_id,kind);
DO $$ BEGIN
 IF NOT EXISTS(SELECT 1 FROM pg_trigger WHERE tgname='research_supplements_immutable') THEN
  CREATE TRIGGER research_supplements_immutable BEFORE UPDATE OR DELETE ON research_supplements
   FOR EACH ROW EXECUTE FUNCTION reject_evidence_mutation();
 END IF;
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='nsai_app') THEN
  GRANT SELECT,INSERT ON research_supplements TO nsai_app;
 END IF;
END $$;
