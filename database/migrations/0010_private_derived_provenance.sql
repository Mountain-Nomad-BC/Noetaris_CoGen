-- Unknown old provenance is never promoted into individual-user visibility.
DO $$ DECLARE tab text; BEGIN
  FOREACH tab IN ARRAY ARRAY['session_messages','invocation_receipts','inference_runs',
    'governed_records','learning_proposals','audit_events','document_knowledge',
    'knowledge_embeddings','research_supplements','claims'] LOOP
    EXECUTE format('ALTER TABLE %I ADD COLUMN source_ids text[] NOT NULL DEFAULT ARRAY[]::text[]',tab);
    EXECUTE format('ALTER TABLE %I ADD COLUMN provenance_complete boolean NOT NULL DEFAULT false',tab);
    EXECUTE format('ALTER TABLE %I ADD CONSTRAINT %I CHECK(cardinality(source_ids)<=1000 AND array_position(source_ids,NULL) IS NULL)',tab,tab||'_source_set');
  END LOOP;
END $$;

-- A row-lock wait must not preserve an expiry decision from statement start.
CREATE OR REPLACE FUNCTION nsai_private_can_read(doc text,actor text) RETURNS boolean
LANGUAGE sql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  SELECT EXISTS(SELECT 1 FROM public.document_owners o WHERE o.document_id=doc AND
    (o.owner_actor=actor OR EXISTS(SELECT 1 FROM public.document_read_grants g
      WHERE g.document_id=doc AND NOT g.revoked
        AND (g.expires_at IS NULL OR g.expires_at>clock_timestamp())
        AND ((g.subject_kind='user' AND g.subject_id=actor) OR
          (g.subject_kind='group' AND EXISTS(SELECT 1 FROM public.private_group_members m
            WHERE m.group_id=g.subject_id AND m.actor=actor))))));
$$;

CREATE FUNCTION nsai_sources_visible(sources text[], complete boolean) RETURNS boolean
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE source_id text;
BEGIN
  IF complete IS DISTINCT FROM true OR sources IS NULL OR cardinality(sources)>1000
     OR coalesce(array_ndims(sources),1)<>1 OR array_position(sources,NULL) IS NOT NULL
    THEN RETURN false; END IF;
  FOREACH source_id IN ARRAY sources LOOP
    IF NOT EXISTS(SELECT 1 FROM public.documents WHERE id=source_id)
      OR NOT public.nsai_document_visible(source_id) THEN RETURN false; END IF;
  END LOOP;
  RETURN true;
END $$;

CREATE FUNCTION nsai_artifact_visible(author_id text,sources text[],complete boolean,reviewable boolean)
RETURNS boolean LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,public AS $$
BEGIN
  IF public.nsai_legacy_context() THEN
    RETURN author_id NOT LIKE 'local-user-%' AND
      (NOT complete OR public.nsai_sources_visible(sources,complete));
  END IF;
  RETURN (author_id=public.nsai_actor() OR
      (reviewable AND public.nsai_actor_role() IN ('reviewer','admin')))
    AND public.nsai_sources_visible(sources,complete);
END $$;

-- A review/supersession can itself depend on another private source. Do not
-- expose that state through a previously shared primary claim after revocation.
DROP POLICY source_read ON claims;
CREATE POLICY claim_read ON claims FOR SELECT USING
  (nsai_document_visible(document_id) AND
    (status='candidate' OR (nsai_legacy_context() AND NOT provenance_complete) OR
      (document_id=ANY(source_ids) AND nsai_sources_visible(source_ids,provenance_complete))));
DROP POLICY source_create ON claims;
CREATE POLICY claim_create ON claims FOR INSERT WITH CHECK
  (nsai_document_visible(document_id) AND (nsai_legacy_context() OR status='candidate'));
DROP POLICY claim_review ON claims;
CREATE POLICY claim_review ON claims FOR UPDATE USING
  (nsai_document_visible(document_id) AND (nsai_legacy_context() OR nsai_actor_role() IN ('reviewer','admin')))
  WITH CHECK(nsai_document_visible(document_id) AND
    (nsai_legacy_context() OR (document_id=ANY(source_ids) AND nsai_sources_visible(source_ids,provenance_complete))));

DROP POLICY message_legacy ON session_messages;
CREATE POLICY message_read ON session_messages FOR SELECT USING
  (EXISTS(SELECT 1 FROM sessions WHERE id=session_id) AND
    ((nsai_legacy_context() AND NOT provenance_complete) OR nsai_sources_visible(source_ids,provenance_complete)));
CREATE POLICY message_create ON session_messages FOR INSERT WITH CHECK
  (EXISTS(SELECT 1 FROM sessions WHERE id=session_id) AND
    ((nsai_legacy_context() AND NOT provenance_complete) OR nsai_sources_visible(source_ids,provenance_complete)));

DROP POLICY invocation_legacy ON invocation_receipts;
CREATE POLICY invocation_read ON invocation_receipts FOR SELECT USING
  ((nsai_legacy_context() AND actor NOT LIKE 'local-user-%') OR
    (actor=nsai_actor() AND (response IS NULL OR nsai_sources_visible(source_ids,provenance_complete))));
CREATE POLICY invocation_create ON invocation_receipts FOR INSERT WITH CHECK
  ((nsai_legacy_context() AND actor NOT LIKE 'local-user-%') OR
    (actor=nsai_actor() AND (response IS NULL OR nsai_sources_visible(source_ids,provenance_complete))));
CREATE POLICY invocation_finish ON invocation_receipts FOR UPDATE USING
  ((nsai_legacy_context() AND actor NOT LIKE 'local-user-%') OR actor=nsai_actor()) WITH CHECK
  ((nsai_legacy_context() AND actor NOT LIKE 'local-user-%') OR
    (actor=nsai_actor() AND (response IS NULL OR nsai_sources_visible(source_ids,provenance_complete))));

DROP POLICY inference_legacy ON inference_runs;
CREATE POLICY inference_read ON inference_runs FOR SELECT USING
  ((nsai_legacy_context() AND actor NOT LIKE 'local-user-%') OR
    (actor=nsai_actor() AND (state='reserved' OR nsai_sources_visible(source_ids,provenance_complete))));
CREATE POLICY inference_create ON inference_runs FOR INSERT WITH CHECK
  ((nsai_legacy_context() AND actor NOT LIKE 'local-user-%') OR (actor=nsai_actor() AND state='reserved'));
CREATE POLICY inference_finish ON inference_runs FOR UPDATE USING
  ((nsai_legacy_context() AND actor NOT LIKE 'local-user-%') OR actor=nsai_actor()) WITH CHECK
  ((nsai_legacy_context() AND actor NOT LIKE 'local-user-%') OR
    (actor=nsai_actor() AND (state='reserved' OR nsai_sources_visible(source_ids,provenance_complete))));

DROP POLICY governed_legacy ON governed_records;
CREATE POLICY governed_read ON governed_records FOR SELECT USING
  (document_id IS NOT NULL AND nsai_document_visible(document_id) AND
    nsai_artifact_visible(author,source_ids,provenance_complete,true));
CREATE POLICY governed_create ON governed_records FOR INSERT WITH CHECK
  (document_id IS NOT NULL AND nsai_document_visible(document_id) AND
    ((nsai_legacy_context() AND author NOT LIKE 'local-user-%') OR
      (author=nsai_actor() AND document_id=ANY(source_ids) AND nsai_sources_visible(source_ids,provenance_complete))));

DROP POLICY learning_legacy ON learning_proposals;
CREATE POLICY learning_read ON learning_proposals FOR SELECT USING
  (EXISTS(SELECT 1 FROM claims WHERE id=source_claim_id) AND
    nsai_artifact_visible(author,source_ids,provenance_complete,true));
CREATE POLICY learning_create ON learning_proposals FOR INSERT WITH CHECK
  (EXISTS(SELECT 1 FROM claims WHERE id=source_claim_id AND
    ((nsai_legacy_context() AND author NOT LIKE 'local-user-%') OR
      (author=nsai_actor() AND document_id=ANY(source_ids) AND nsai_sources_visible(source_ids,provenance_complete)))));
CREATE POLICY learning_review ON learning_proposals FOR UPDATE USING
  (EXISTS(SELECT 1 FROM claims WHERE id=source_claim_id) AND
    (nsai_legacy_context() OR nsai_actor_role() IN ('reviewer','admin')) AND
    nsai_artifact_visible(author,source_ids,provenance_complete,true)) WITH CHECK
  (EXISTS(SELECT 1 FROM claims WHERE id=source_claim_id) AND
    nsai_artifact_visible(author,source_ids,provenance_complete,true));

DROP POLICY audit_legacy_read ON audit_events;
CREATE POLICY audit_scoped_read ON audit_events FOR SELECT USING
  (nsai_artifact_visible(actor,source_ids,provenance_complete,false));
DROP POLICY audit_create ON audit_events;
CREATE POLICY audit_scoped_create ON audit_events FOR INSERT WITH CHECK
  ((nsai_legacy_context() AND actor NOT LIKE 'local-user-%') OR
    (actor=nsai_actor() AND nsai_sources_visible(source_ids,provenance_complete)));

DO $$ DECLARE tab text; BEGIN
  FOREACH tab IN ARRAY ARRAY['document_knowledge','knowledge_embeddings','research_supplements'] LOOP
    EXECUTE format('DROP POLICY source_read ON %I',tab);
    EXECUTE format('DROP POLICY source_create ON %I',tab);
    EXECUTE format('CREATE POLICY artifact_read ON %I FOR SELECT USING(public.nsai_document_visible(document_id) AND ((public.nsai_legacy_context() AND NOT provenance_complete) OR (document_id=ANY(source_ids) AND public.nsai_sources_visible(source_ids,provenance_complete))))',tab);
    EXECUTE format('CREATE POLICY artifact_create ON %I FOR INSERT WITH CHECK(public.nsai_document_visible(document_id) AND ((public.nsai_legacy_context() AND NOT provenance_complete) OR (document_id=ANY(source_ids) AND public.nsai_sources_visible(source_ids,provenance_complete))))',tab);
  END LOOP;
END $$;

-- Preserve the existing global daily budget without exposing other actors'
-- source-bearing inference rows to the calling application's query.
CREATE FUNCTION nsai_daily_inference_count() RETURNS bigint LANGUAGE sql STABLE
SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  SELECT count(*) FROM public.inference_runs
    WHERE created_at>=date_trunc('day',now() AT TIME ZONE 'UTC') AT TIME ZONE 'UTC';
$$;
CREATE FUNCTION nsai_current_source_dependencies() RETURNS SETOF text
LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  SELECT document_id FROM public.private_transaction_reads
    WHERE transaction_id=pg_current_xact_id() AND actor=public.nsai_actor();
$$;
REVOKE ALL ON FUNCTION nsai_sources_visible(text[],boolean),
  nsai_artifact_visible(text,text[],boolean,boolean),nsai_daily_inference_count(),
  nsai_current_source_dependencies() FROM PUBLIC;
