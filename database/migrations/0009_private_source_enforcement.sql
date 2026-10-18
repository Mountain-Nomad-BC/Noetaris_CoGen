-- Source enforcement is installed while individual-user HTTP admission remains
-- closed. Unintegrated derived paths fail closed for individual principals.
ALTER TABLE documents ADD COLUMN owner_scope text NOT NULL DEFAULT 'legacy-shared';
ALTER TABLE documents ADD CONSTRAINT documents_owner_scope_shape CHECK
  (owner_scope='legacy-shared' OR owner_scope ~ '^local-user-[a-z][a-z0-9_-]{0,63}$');
-- Keep the original conflict target for the prior application version. Private
-- logical copies use a disjoint internal key; original_sha256 retains custody.
ALTER TABLE documents ADD CONSTRAINT documents_owner_hash_revision_key
  UNIQUE(owner_scope,sha256,source_version);

CREATE FUNCTION nsai_actor() RETURNS text LANGUAGE sql STABLE AS $$
  SELECT coalesce(nullif(current_setting('nsai.actor',true),''),'legacy-service');
$$;
CREATE FUNCTION nsai_actor_role() RETURNS text LANGUAGE sql STABLE AS $$
  SELECT coalesce(nullif(current_setting('nsai.role',true),''),'service');
$$;
CREATE FUNCTION nsai_legacy_context() RETURNS boolean LANGUAGE sql STABLE AS $$
  SELECT public.nsai_actor() IN ('legacy-service','local-operator','local-viewer','local-reviewer','local-admin');
$$;
CREATE FUNCTION nsai_private_source_key() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
BEGIN
  IF NEW.owner_scope='legacy-shared' THEN
    IF NEW.sha256 LIKE 'private/1/%' THEN
      RAISE EXCEPTION 'Invalid source key' USING ERRCODE='42501';
    END IF;
  ELSE
    NEW.original_sha256=coalesce(NEW.original_sha256,NEW.sha256);
    NEW.sha256='private/1/' || NEW.owner_scope || '/' || NEW.original_sha256;
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER private_source_key BEFORE INSERT ON documents
  FOR EACH ROW EXECUTE FUNCTION nsai_private_source_key();
CREATE FUNCTION nsai_source_scope_allows(doc text) RETURNS boolean LANGUAGE sql VOLATILE AS $$
  SELECT coalesce(current_setting('nsai.job_id',true),'')='';
$$;

-- Records successful per-transaction private authorization. Only the database
-- owner may maintain this table. No app table/sequence access is granted.
CREATE TABLE private_transaction_reads (
  transaction_id xid8 NOT NULL,
  document_id text NOT NULL REFERENCES document_owners(document_id),
  actor text NOT NULL,
  epoch bigint NOT NULL CHECK(epoch>0),
  created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  PRIMARY KEY(transaction_id,document_id,actor)
);

CREATE FUNCTION nsai_document_visible(doc text) RETURNS boolean
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE owner_id text; actor_id text; policy_epoch bigint;
BEGIN
  IF NOT public.nsai_source_scope_allows(doc) THEN RETURN false; END IF;
  SELECT owner_actor INTO owner_id FROM public.document_owners WHERE document_id=doc;
  IF owner_id IS NULL THEN RETURN public.nsai_legacy_context(); END IF;
  actor_id=public.nsai_actor();
  IF actor_id !~ '^local-user-[a-z][a-z0-9_-]{0,63}$'
    OR public.nsai_actor_role() NOT IN ('operator','viewer','reviewer','admin')
    OR NOT public.nsai_private_can_read(doc,actor_id) THEN RETURN false; END IF;
  IF NOT EXISTS(SELECT 1 FROM public.private_transaction_reads
      WHERE transaction_id=pg_current_xact_id() AND document_id=doc AND actor=actor_id) THEN
    -- Locks source policy and contributing groups through transaction commit.
    -- Admin reads insert their audit here, before the caller can commit bytes.
    policy_epoch=public.nsai_private_authorize_read(doc,actor_id,public.nsai_actor_role());
    INSERT INTO public.private_transaction_reads(transaction_id,document_id,actor,epoch)
      VALUES(pg_current_xact_id(),doc,actor_id,policy_epoch) ON CONFLICT DO NOTHING;
  END IF;
  RETURN true;
END $$;

CREATE FUNCTION nsai_private_source_owner() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
BEGIN
  IF NEW.owner_scope <> 'legacy-shared' THEN
    IF NEW.owner_scope <> public.nsai_actor() OR NEW.ingested_by <> public.nsai_actor()
      THEN RAISE EXCEPTION 'Invalid source owner' USING ERRCODE='42501'; END IF;
    PERFORM public.nsai_private_own(NEW.id,NEW.owner_scope);
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER private_source_owner AFTER INSERT ON documents
  FOR EACH ROW EXECUTE FUNCTION nsai_private_source_owner();

ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
-- INSERT .. ON CONFLICT checks SELECT policy on the proposed tuple before the
-- AFTER INSERT owner trigger can run. This exception applies only until the
-- immutable owner exists; committed reads always pass the policy/audit path.
CREATE FUNCTION nsai_pending_source_insert(doc text,scope text,creator text) RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  SELECT scope=public.nsai_actor() AND creator=public.nsai_actor()
    AND public.nsai_actor_role()='operator'
    AND NOT EXISTS(SELECT 1 FROM public.document_owners WHERE document_id=doc);
$$;
CREATE POLICY documents_read ON documents FOR SELECT USING
  (nsai_document_visible(id) OR nsai_pending_source_insert(id,owner_scope,ingested_by));
CREATE POLICY documents_create ON documents FOR INSERT WITH CHECK
  ((nsai_legacy_context() AND owner_scope='legacy-shared' AND ingested_by NOT LIKE 'local-user-%')
   OR (NOT nsai_legacy_context() AND owner_scope=nsai_actor() AND ingested_by=nsai_actor()
       AND nsai_actor_role()='operator'));

DO $$ DECLARE tab text; BEGIN
  FOREACH tab IN ARRAY ARRAY['claims','source_spans','chunks','document_knowledge',
                            'knowledge_embeddings','research_supplements'] LOOP
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY',tab);
    EXECUTE format('CREATE POLICY source_read ON %I FOR SELECT USING(public.nsai_document_visible(document_id))',tab);
    EXECUTE format('CREATE POLICY source_create ON %I FOR INSERT WITH CHECK(public.nsai_document_visible(document_id))',tab);
  END LOOP;
END $$;
CREATE POLICY claim_review ON claims FOR UPDATE USING
  (nsai_document_visible(document_id) AND (nsai_legacy_context() OR nsai_actor_role() IN ('reviewer','admin')))
  WITH CHECK(nsai_document_visible(document_id));
ALTER TABLE claim_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY claim_event_read ON claim_events FOR SELECT USING
  (EXISTS(SELECT 1 FROM claims WHERE id=claim_id));
CREATE POLICY claim_event_create ON claim_events FOR INSERT WITH CHECK
  (EXISTS(SELECT 1 FROM claims WHERE id=claim_id));

-- Complete provenance for these records is installed by the next integration
-- migration. Until then only legacy records in legacy context remain available.
ALTER TABLE governed_records ENABLE ROW LEVEL SECURITY;
CREATE POLICY governed_legacy ON governed_records FOR ALL USING
  (nsai_legacy_context() AND author NOT LIKE 'local-user-%'
    AND document_id IS NOT NULL AND nsai_document_visible(document_id))
  WITH CHECK(nsai_legacy_context() AND author NOT LIKE 'local-user-%'
    AND document_id IS NOT NULL AND nsai_document_visible(document_id));
ALTER TABLE governed_reviews ENABLE ROW LEVEL SECURITY;
CREATE POLICY governed_review_legacy ON governed_reviews FOR ALL USING
  (EXISTS(SELECT 1 FROM governed_records WHERE id=record_id))
  WITH CHECK(EXISTS(SELECT 1 FROM governed_records WHERE id=record_id));
ALTER TABLE learning_proposals ENABLE ROW LEVEL SECURITY;
CREATE POLICY learning_legacy ON learning_proposals FOR ALL USING
  (nsai_legacy_context() AND author NOT LIKE 'local-user-%'
    AND EXISTS(SELECT 1 FROM claims WHERE id=source_claim_id))
  WITH CHECK(nsai_legacy_context() AND author NOT LIKE 'local-user-%'
    AND EXISTS(SELECT 1 FROM claims WHERE id=source_claim_id));
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
CREATE POLICY session_scope ON sessions FOR ALL USING
  ((nsai_legacy_context() AND owner NOT LIKE 'local-user-%') OR owner=nsai_actor())
  WITH CHECK((nsai_legacy_context() AND owner NOT LIKE 'local-user-%') OR owner=nsai_actor());
ALTER TABLE session_messages ENABLE ROW LEVEL SECURITY;
CREATE POLICY message_legacy ON session_messages FOR ALL USING
  (nsai_legacy_context() AND EXISTS(SELECT 1 FROM sessions WHERE id=session_id))
  WITH CHECK(nsai_legacy_context() AND EXISTS(SELECT 1 FROM sessions WHERE id=session_id));
ALTER TABLE invocation_receipts ENABLE ROW LEVEL SECURITY;
CREATE POLICY invocation_legacy ON invocation_receipts FOR ALL USING
  (nsai_legacy_context() AND actor NOT LIKE 'local-user-%')
  WITH CHECK(nsai_legacy_context() AND actor NOT LIKE 'local-user-%');
ALTER TABLE inference_runs ENABLE ROW LEVEL SECURITY;
CREATE POLICY inference_legacy ON inference_runs FOR ALL USING
  (nsai_legacy_context() AND actor NOT LIKE 'local-user-%')
  WITH CHECK(nsai_legacy_context() AND actor NOT LIKE 'local-user-%');

ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY audit_legacy_read ON audit_events FOR SELECT USING
  (nsai_legacy_context() AND actor NOT LIKE 'local-user-%');
CREATE POLICY audit_create ON audit_events FOR INSERT WITH CHECK
  ((nsai_legacy_context() AND actor NOT LIKE 'local-user-%') OR actor=nsai_actor());
-- Appending the global chain needs only the last hash, never a private payload.
CREATE FUNCTION nsai_audit_head() RETURNS text LANGUAGE sql STABLE SECURITY DEFINER
SET search_path=pg_catalog,public AS $$
  SELECT coalesce((SELECT sha256 FROM public.audit_events ORDER BY id DESC LIMIT 1),repeat('0',64));
$$;

REVOKE ALL ON FUNCTION nsai_document_visible(text),nsai_private_source_owner(),
  nsai_private_source_key(),
  nsai_audit_head(),nsai_actor(),nsai_actor_role(),nsai_legacy_context(),
  nsai_pending_source_insert(text,text,text),nsai_source_scope_allows(text) FROM PUBLIC;
