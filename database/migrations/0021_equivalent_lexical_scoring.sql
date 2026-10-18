-- Preserve cover-density scores while avoiding provably zero/repeated work.
CREATE OR REPLACE FUNCTION nsai_library_lexical_search(exact_query text,alternate_query text,entity_filter text,
  selected text[],revision_filter text,page_filter integer[],result_limit integer)
RETURNS SETOF jsonb LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path=pg_catalog,public AS $$
DECLARE exact_terms tsquery; alternate_terms tsquery; entity_terms tsquery;
BEGIN
  IF coalesce(current_setting('nsai.job_id',true),'')<>'' THEN
    RAISE EXCEPTION 'Request context required' USING ERRCODE='42501'; END IF;
  IF exact_query IS NULL OR length(exact_query)>1000 OR alternate_query IS NULL OR length(alternate_query)>8000
    OR (entity_filter IS NOT NULL AND length(entity_filter)>8000)
    OR result_limit IS NULL OR result_limit NOT BETWEEN 1 AND 51
    OR (selected IS NOT NULL AND (cardinality(selected) NOT BETWEEN 1 AND 1000 OR array_ndims(selected)<>1 OR array_position(selected,NULL) IS NOT NULL))
    OR (page_filter IS NOT NULL AND (cardinality(page_filter) NOT BETWEEN 1 AND 100 OR array_ndims(page_filter)<>1 OR array_position(page_filter,NULL) IS NOT NULL
      OR EXISTS(SELECT 1 FROM unnest(page_filter) p WHERE p NOT BETWEEN 1 AND 100)))
    THEN RAISE EXCEPTION 'Invalid lexical search bounds'; END IF;
  exact_terms=plainto_tsquery('english',exact_query);
  alternate_terms=websearch_to_tsquery('english',alternate_query);
  IF entity_filter IS NOT NULL THEN entity_terms=websearch_to_tsquery('english',entity_filter); END IF;
  RETURN QUERY
  WITH authorized AS MATERIALIZED (
    SELECT d.id FROM public.documents d
    WHERE (selected IS NULL OR d.id=ANY(selected))
      AND (revision_filter IS NULL OR d.source_version=revision_filter)
      AND public.nsai_index_source_readable(d.id)
  ), ranked AS MATERIALIZED (
    SELECT c.id,c.document_id,
      CASE WHEN exact_terms=alternate_terms THEN ts_rank_cd(c.search,exact_terms)*1.25
           ELSE (CASE WHEN c.search @@ exact_terms THEN ts_rank_cd(c.search,exact_terms) ELSE 0::real END)
             +(CASE WHEN c.search @@ alternate_terms THEN ts_rank_cd(c.search,alternate_terms) ELSE 0::real END)*0.25 END AS score
    FROM authorized d JOIN public.chunks c ON c.document_id=d.id
    WHERE (c.search @@ exact_terms OR c.search @@ alternate_terms)
      AND (entity_filter IS NULL OR c.search @@ entity_terms)
      AND (page_filter IS NULL OR (c.locator LIKE 'page:%' AND split_part(c.locator,':',2)=ANY(SELECT p::text FROM unnest(page_filter) p)))
    ORDER BY score DESC,c.id LIMIT result_limit
  )
  SELECT jsonb_build_object('id',c.id,'document_id',d.id,'title',d.title,'revision',d.source_version,
    'original_sha256',d.original_sha256,'media_type',d.media_type,'locator',c.locator,'text',c.text,'sha256',c.sha256,
    'page_coverage',d.manifest#>'{documents,0,metadata,pages}',
    'extraction_complete',CASE WHEN d.media_type='application/pdf' THEN coalesce((d.manifest#>>'{documents,0,metadata,complete}')::boolean,false) ELSE true END,
    'score',r.score)
  FROM ranked r JOIN public.chunks c ON c.id=r.id JOIN public.documents d ON d.id=r.document_id
  ORDER BY r.score DESC,r.id;
END $$;
REVOKE ALL ON FUNCTION nsai_library_lexical_search(text,text,text,text[],text,integer[],integer) FROM PUBLIC;
