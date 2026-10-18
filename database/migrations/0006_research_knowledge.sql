-- Source-derived research artifacts remain observations; no automatic canon promotion.
CREATE TABLE IF NOT EXISTS document_knowledge (
 document_id TEXT PRIMARY KEY REFERENCES documents(id),
 source_sha256 TEXT NOT NULL CHECK(source_sha256 ~ '^[0-9a-f]{64}$'),
 revision TEXT NOT NULL,
 knowledge JSONB NOT NULL CHECK(jsonb_typeof(knowledge)='object'),
 formulas JSONB NOT NULL CHECK(jsonb_typeof(formulas)='object'),
 artifact_sha256 TEXT NOT NULL CHECK(artifact_sha256 ~ '^[0-9a-f]{64}$'),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS knowledge_embeddings (
 document_id TEXT NOT NULL REFERENCES document_knowledge(document_id),
 model_sha256 TEXT NOT NULL CHECK(model_sha256 ~ '^[0-9a-f]{64}$'),
 artifact_sha256 TEXT NOT NULL CHECK(artifact_sha256 ~ '^[0-9a-f]{64}$'),
 payload JSONB NOT NULL CHECK(jsonb_typeof(payload)='object'),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 PRIMARY KEY(document_id,model_sha256)
);
DO $$ DECLARE entry TEXT; BEGIN
 FOREACH entry IN ARRAY ARRAY['document_knowledge','knowledge_embeddings'] LOOP
  IF NOT EXISTS(SELECT 1 FROM pg_trigger WHERE tgname=entry||'_immutable') THEN
   EXECUTE format('CREATE TRIGGER %I BEFORE UPDATE OR DELETE ON %I FOR EACH ROW EXECUTE FUNCTION reject_evidence_mutation()',entry||'_immutable',entry);
  END IF;
 END LOOP;
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='nsai_app') THEN
  GRANT SELECT,INSERT ON document_knowledge,knowledge_embeddings TO nsai_app;
 END IF;
END $$;
