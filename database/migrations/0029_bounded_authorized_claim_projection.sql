-- Authorize each primary source and distinct review-dependency set before
-- projecting claim payloads. Duplicated observations must not repeat policy
-- queries thousands of times. Raw app-table RLS remains unchanged.
CREATE INDEX claims_source_span ON claims(document_id,locator);
CREATE FUNCTION nsai_readable_claim_projection(selected text[],revision_filter text,page_filter integer[],active_only boolean)
RETURNS TABLE(id text,subject text,predicate text,value text,locator text,document_id text,
  revision integer,reviewed_by text,status text,source_ids text[],provenance_complete boolean,original_sha256 text,created_at timestamptz)
LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path=pg_catalog,public SET plan_cache_mode=force_custom_plan AS $$
BEGIN
  IF coalesce(current_setting('nsai.job_id',true),'')<>'' THEN
    RAISE EXCEPTION 'Request context required' USING ERRCODE='42501'; END IF;
  IF active_only IS NULL OR (revision_filter IS NOT NULL AND length(revision_filter) NOT BETWEEN 1 AND 50)
    OR (selected IS NOT NULL AND (cardinality(selected) NOT BETWEEN 1 AND 1000 OR array_ndims(selected)<>1
      OR array_lower(selected,1)<>1 OR array_position(selected,NULL) IS NOT NULL
      OR EXISTS(SELECT 1 FROM unnest(selected) item WHERE length(item) NOT BETWEEN 1 AND 200)))
    OR (page_filter IS NOT NULL AND (cardinality(page_filter) NOT BETWEEN 1 AND 100 OR array_ndims(page_filter)<>1
      OR array_lower(page_filter,1)<>1 OR array_position(page_filter,NULL) IS NOT NULL
      OR EXISTS(SELECT 1 FROM unnest(page_filter) item WHERE item NOT BETWEEN 1 AND 1000))) THEN
    RAISE EXCEPTION 'Invalid claim scope' USING ERRCODE='22023'; END IF;
  RETURN QUERY
  WITH parent_ids AS MATERIALIZED (
    SELECT DISTINCT c.document_id FROM public.claims c
      WHERE (NOT active_only OR c.status NOT IN ('superseded','rejected'))
        AND (selected IS NULL OR c.document_id=ANY(selected))
  ), permitted AS MATERIALIZED (
    SELECT p.document_id FROM parent_ids p
      WHERE public.nsai_index_source_readable(p.document_id)
  ), primary_rows AS MATERIALIZED (
    SELECT c.id,c.subject,c.predicate,c.value,c.locator,c.document_id,c.revision,
      c.reviewed_by,c.status,c.source_ids,c.provenance_complete,d.original_sha256,c.created_at
    FROM permitted p
    CROSS JOIN LATERAL (
      SELECT d.original_sha256 FROM public.documents d WHERE d.id=p.document_id
        AND (revision_filter IS NULL OR d.source_version=revision_filter) OFFSET 0
    ) d
    CROSS JOIN LATERAL (
      SELECT c.* FROM public.claims c WHERE c.document_id=p.document_id
        AND (NOT active_only OR c.status NOT IN ('superseded','rejected'))
        AND (page_filter IS NULL OR (c.locator LIKE 'page:%'
          AND split_part(c.locator,':',2)=ANY(ARRAY(SELECT item::text FROM unnest(page_filter) item)))) OFFSET 0
    ) c
  ), dependency_keys AS MATERIALIZED (
    SELECT DISTINCT c.document_id,(c.status='candidate') AS candidate,c.source_ids,c.provenance_complete
      FROM primary_rows c
  ), allowed_dependencies AS MATERIALIZED (
    SELECT k.* FROM dependency_keys k WHERE CASE
      WHEN k.candidate THEN true
      WHEN public.nsai_legacy_context() AND NOT k.provenance_complete THEN true
      ELSE k.document_id=ANY(k.source_ids) AND public.nsai_sources_visible(k.source_ids,k.provenance_complete)
    END
  )
  SELECT c.* FROM primary_rows c JOIN allowed_dependencies k
    ON k.document_id=c.document_id AND k.candidate=(c.status='candidate')
      AND k.source_ids IS NOT DISTINCT FROM c.source_ids
      AND k.provenance_complete=c.provenance_complete;
END $$;
REVOKE ALL ON FUNCTION nsai_readable_claim_projection(text[],text,integer[],boolean) FROM PUBLIC;

CREATE FUNCTION nsai_claim_context(spans jsonb,selected text[],revision_filter text,page_filter integer[])
RETURNS SETOF jsonb LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path=pg_catalog,public SET plan_cache_mode=force_custom_plan AS $$
BEGIN
  IF spans IS NULL OR jsonb_typeof(spans)<>'array' THEN
    RAISE EXCEPTION 'Invalid passage scope' USING ERRCODE='22023'; END IF;
  IF jsonb_array_length(spans) NOT BETWEEN 1 AND 2000 OR octet_length(spans::text)>1048576
    OR EXISTS(SELECT 1 FROM jsonb_array_elements(spans) item WHERE
      jsonb_typeof(item)<>'object' OR jsonb_typeof(item->'document_id') IS DISTINCT FROM 'string'
      OR jsonb_typeof(item->'locator') IS DISTINCT FROM 'string'
      OR (item-'document_id'-'locator')<>'{}'::jsonb
      OR length(item->>'document_id') NOT BETWEEN 1 AND 200
      OR length(item->>'locator') NOT BETWEEN 1 AND 200) THEN
    RAISE EXCEPTION 'Invalid passage scope' USING ERRCODE='22023'; END IF;
  RETURN QUERY
  WITH selected_spans AS MATERIALIZED (
    SELECT DISTINCT s.document_id,s.locator FROM jsonb_to_recordset(spans) AS s(document_id text,locator text)
  ), readable AS MATERIALIZED (
    SELECT c.id,c.subject,c.predicate,c.value,c.locator,c.document_id,c.revision,
      c.reviewed_by,c.status,c.source_ids,c.provenance_complete,c.original_sha256
      FROM public.nsai_readable_claim_projection(selected,revision_filter,page_filter,true) c
  ), seeds AS MATERIALIZED (
    SELECT DISTINCT ON (c.document_id,c.locator,c.subject,c.predicate,c.value,c.status) c.*
      FROM readable c JOIN selected_spans s ON s.document_id=c.document_id AND s.locator=c.locator
      ORDER BY c.document_id,c.locator,c.subject,c.predicate,c.value,c.status,c.id
  ), witnesses AS (
    SELECT DISTINCT ON (c.subject,c.predicate,c.value) c.* FROM readable c
      WHERE EXISTS(SELECT 1 FROM seeds s WHERE s.subject=c.subject AND s.predicate=c.predicate)
      ORDER BY c.subject,c.predicate,c.value,(c.status='verified') DESC,c.id
  )
  SELECT to_jsonb(context) FROM (SELECT * FROM seeds UNION SELECT * FROM witnesses) context
    ORDER BY context.id LIMIT 2001;
END $$;
REVOKE ALL ON FUNCTION nsai_claim_context(jsonb,text[],text,integer[]) FROM PUBLIC;

CREATE FUNCTION nsai_memory_claim_seeds(question text,selected text[],revision_filter text,page_filter integer[])
RETURNS SETOF jsonb LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path=pg_catalog,public SET plan_cache_mode=force_custom_plan AS $$
BEGIN
  IF question IS NULL OR length(question)>1000 THEN
    RAISE EXCEPTION 'Invalid memory question' USING ERRCODE='22023'; END IF;
  RETURN QUERY
  SELECT jsonb_build_object('document_id',c.document_id,'locator',c.locator)
    FROM public.nsai_readable_claim_projection(selected,revision_filter,page_filter,true) c
    ORDER BY ts_rank_cd(to_tsvector('english',c.subject||' '||c.predicate||' '||c.value),
      websearch_to_tsquery('english',question)) DESC,(c.status='verified') DESC,c.id LIMIT 12;
END $$;
REVOKE ALL ON FUNCTION nsai_memory_claim_seeds(text,text[],text,integer[]) FROM PUBLIC;

CREATE FUNCTION nsai_claim_review_page(page_limit integer,before_time timestamptz,before_id text)
RETURNS jsonb LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path=pg_catalog,public SET plan_cache_mode=force_custom_plan AS $$
DECLARE result jsonb;
BEGIN
  IF page_limit IS NULL OR page_limit NOT BETWEEN 1 AND 100
    OR (before_time IS NULL)<>(before_id IS NULL)
    OR (before_id IS NOT NULL AND length(before_id) NOT BETWEEN 1 AND 200) THEN
    RAISE EXCEPTION 'Invalid claim page' USING ERRCODE='22023'; END IF;
  WITH readable AS MATERIALIZED (
    SELECT * FROM public.nsai_readable_claim_projection(NULL,NULL,NULL,false)
  ), displayed AS (
    SELECT c.id,c.document_id,c.subject,c.predicate,c.value,c.locator,c.status,c.revision,
      c.reviewed_by,c.source_ids,c.provenance_complete,c.created_at FROM readable c
    WHERE before_time IS NULL OR (c.created_at,c.id)<(before_time,before_id)
    ORDER BY c.created_at DESC,c.id DESC LIMIT page_limit+1
  ), witnesses AS (
    SELECT DISTINCT ON(c.subject,c.predicate,c.value,(c.status NOT IN ('rejected','superseded')))
      c.id,c.document_id,c.subject,c.predicate,c.value,c.locator,c.status FROM readable c
    ORDER BY c.subject,c.predicate,c.value,(c.status NOT IN ('rejected','superseded')),
      (c.status='verified') DESC,c.id LIMIT 2001
  )
  SELECT jsonb_build_object('total',(SELECT count(*) FROM readable),
    'verified',(SELECT count(*) FROM readable WHERE status='verified'),
    'items',coalesce((SELECT jsonb_agg(to_jsonb(d) ORDER BY d.created_at DESC,d.id DESC) FROM displayed d),'[]'::jsonb),
    'witnesses',coalesce((SELECT jsonb_agg(to_jsonb(w)) FROM witnesses w),'[]'::jsonb)) INTO result;
  RETURN result;
END $$;
REVOKE ALL ON FUNCTION nsai_claim_review_page(integer,timestamptz,text) FROM PUBLIC;

CREATE FUNCTION nsai_reflection_claims() RETURNS SETOF jsonb
LANGUAGE sql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  SELECT to_jsonb(c)-'original_sha256'-'created_at'
    FROM public.nsai_readable_claim_projection(NULL,NULL,NULL,false) c
    ORDER BY c.created_at,c.id LIMIT 2001;
$$;
REVOKE ALL ON FUNCTION nsai_reflection_claims() FROM PUBLIC;
