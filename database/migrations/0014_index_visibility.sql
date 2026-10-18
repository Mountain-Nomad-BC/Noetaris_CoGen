-- Source custody is inspectable while processing. Search/knowledge consumers
-- require the atomically published generation; staged vector rows are private.
CREATE FUNCTION nsai_initialize_source_index() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
BEGIN
  INSERT INTO public.source_index_state(document_id,state) VALUES(NEW.id,'queued');
  RETURN NEW;
END $$;
CREATE TRIGGER source_index_initialize AFTER INSERT ON documents
  FOR EACH ROW EXECUTE FUNCTION nsai_initialize_source_index();
INSERT INTO source_index_state(document_id,state)
  SELECT id,'queued' FROM documents WHERE owner_scope<>'legacy-shared'
  ON CONFLICT(document_id) DO NOTHING;

CREATE FUNCTION nsai_source_is_owner(doc text) RETURNS boolean
LANGUAGE sql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  SELECT public.nsai_source_scope_allows(doc) AND EXISTS(SELECT 1 FROM public.document_owners
    WHERE document_id=doc AND owner_actor=public.nsai_actor());
$$;
CREATE FUNCTION nsai_index_source_readable(doc text) RETURNS boolean
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE sources text[];
BEGIN
  IF NOT public.nsai_document_visible(doc) THEN RETURN false; END IF;
  SELECT p.source_ids INTO sources FROM public.source_index_state s
    JOIN public.semantic_publications p ON p.id=s.current_publication_id WHERE s.document_id=doc;
  IF FOUND THEN RETURN public.nsai_sources_visible(sources,true); END IF;
  -- Preserve historical unowned demonstration data, without calling it an
  -- accepted private/semantic generation. Every new source has a queued row.
  RETURN public.nsai_legacy_context()
    AND NOT EXISTS(SELECT 1 FROM public.source_index_state WHERE document_id=doc)
    AND NOT EXISTS(SELECT 1 FROM public.document_owners WHERE document_id=doc);
END $$;

DO $$ DECLARE tab text; BEGIN
  FOREACH tab IN ARRAY ARRAY['document_knowledge','knowledge_embeddings'] LOOP
    EXECUTE format('DROP POLICY artifact_create ON %I',tab);
    EXECUTE format('CREATE POLICY artifact_create ON %I FOR INSERT WITH CHECK(public.nsai_document_visible(document_id) AND (public.nsai_source_is_owner(document_id) OR public.nsai_legacy_context()) AND ((public.nsai_legacy_context() AND NOT provenance_complete) OR (document_id=ANY(source_ids) AND public.nsai_sources_visible(source_ids,provenance_complete))))',tab);
  END LOOP;
END $$;

CREATE OR REPLACE FUNCTION nsai_source_index_status(doc text) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE total_passages bigint; coverage_complete boolean;
BEGIN
  IF NOT EXISTS(SELECT 1 FROM public.documents WHERE id=doc) OR NOT public.nsai_document_visible(doc)
    THEN RAISE EXCEPTION 'Source unavailable' USING ERRCODE='42501'; END IF;
  SELECT (SELECT count(*) FROM jsonb_array_elements(coalesce(k.knowledge->'nodes','[]'::jsonb)) node
    WHERE node->>'kind'='passage'),(k.knowledge#>>'{extraction_coverage,complete}')::boolean
    INTO total_passages,coverage_complete FROM public.document_knowledge k
    WHERE k.document_id=doc AND ((public.nsai_legacy_context() AND NOT k.provenance_complete)
      OR public.nsai_sources_visible(k.source_ids,k.provenance_complete));
  RETURN coalesce((SELECT jsonb_build_object('document_id',doc,'state',s.state,'epoch',s.epoch,
    'ready',s.current_publication_id IS NOT NULL AND public.nsai_index_source_readable(doc),'publication_id',s.current_publication_id,
    'job_id',j.id,'attempts',j.attempts,'error_code',j.error_code,'passages_total',total_passages,
    'source_coverage_complete',coverage_complete,
    'passages_completed',CASE WHEN total_passages IS NULL THEN NULL WHEN s.state='ready' THEN total_passages ELSE
      (SELECT count(*) FROM public.semantic_job_vectors v WHERE v.job_id=j.id) END)
    FROM public.source_index_state s LEFT JOIN public.semantic_jobs j ON j.id=s.pending_job_id WHERE s.document_id=doc),
    jsonb_build_object('document_id',doc,'state','not-commissioned','ready',false));
END $$;
REVOKE ALL ON FUNCTION nsai_initialize_source_index(),nsai_source_is_owner(text),
  nsai_index_source_readable(text) FROM PUBLIC;
