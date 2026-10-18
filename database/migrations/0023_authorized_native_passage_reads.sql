-- Preserve source authorization before vector reads and precompute entity text.
ALTER TABLE native_semantic_passages ADD COLUMN search tsvector
  GENERATED ALWAYS AS (to_tsvector('english',text)) STORED;
CREATE INDEX native_passage_search ON native_semantic_passages USING GIN(search);
CREATE OR REPLACE FUNCTION nsai_library_semantic_search(query_vector double precision[], selected text[],
  revision_filter text, page_filter integer[], entity_filter text, result_limit integer)
RETURNS SETOF jsonb LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path=pg_catalog,public AS $$
DECLARE magnitude double precision;
BEGIN
  IF coalesce(current_setting('nsai.job_id',true),'')<>'' THEN
    RAISE EXCEPTION 'Request context required' USING ERRCODE='42501';
  END IF;
  IF query_vector IS NULL OR cardinality(query_vector)<>384 OR array_ndims(query_vector)<>1
    OR array_lower(query_vector,1)<>1
    OR result_limit IS NULL OR result_limit NOT BETWEEN 1 AND 51
    OR (selected IS NOT NULL AND (cardinality(selected)=0 OR cardinality(selected)>1000
      OR array_position(selected,NULL) IS NOT NULL))
    OR (page_filter IS NOT NULL AND (cardinality(page_filter)=0 OR cardinality(page_filter)>100
      OR array_position(page_filter,NULL) IS NOT NULL
      OR EXISTS(SELECT 1 FROM unnest(page_filter) p WHERE p NOT BETWEEN 1 AND 100)))
    OR EXISTS(SELECT 1 FROM unnest(query_vector) v WHERE v IS NULL OR v::text IN ('NaN','Infinity','-Infinity'))
    THEN RAISE EXCEPTION 'Invalid semantic search bounds'; END IF;
  SELECT sqrt(sum(v*v)) INTO magnitude FROM unnest(query_vector) v;
  IF magnitude IS NULL OR abs(magnitude-1)>0.00001 THEN
    RAISE EXCEPTION 'Normalized query vector required'; END IF;
  RETURN QUERY
  WITH authorized AS MATERIALIZED (
    SELECT d.id,e.model_sha256,e.artifact_sha256
    FROM public.source_index_state s
    JOIN public.semantic_publications p ON p.id=s.current_publication_id AND p.document_id=s.document_id
    JOIN public.documents d ON d.id=s.document_id
    JOIN public.knowledge_embeddings e ON e.document_id=d.id AND e.model_sha256=p.model_sha256
      AND e.artifact_sha256=p.embedding_sha256
    JOIN public.document_knowledge k ON k.document_id=d.id AND k.artifact_sha256=p.knowledge_sha256
    WHERE p.model_sha256='6fd5d72fe4589f189f8ebc006442dbb529bb7ce38f8082112682524616046452'
      AND (selected IS NULL OR d.id=ANY(selected))
      AND (revision_filter IS NULL OR d.source_version=revision_filter)
      AND public.nsai_index_source_readable(d.id)
      AND public.nsai_sources_visible(e.source_ids,e.provenance_complete)
      AND public.nsai_sources_visible(k.source_ids,k.provenance_complete)
  ), candidates AS (
    SELECT a.id,v.node_id,v.locator,v.page,v.text,v.source_segments,score.value AS score
    FROM authorized a
    CROSS JOIN LATERAL (
      -- OFFSET 0 preserves the source-correlated boundary: vector rows are
      -- fetched only after their source passed the authorization CTE.
      SELECT p.* FROM public.native_semantic_passages p
      WHERE p.document_id=a.id AND p.model_sha256=a.model_sha256 AND p.embedding_sha256=a.artifact_sha256
        AND (page_filter IS NULL OR p.page=ANY(page_filter))
        AND (entity_filter IS NULL OR p.search @@ websearch_to_tsquery('english',entity_filter))
      OFFSET 0
    ) v
    CROSS JOIN LATERAL (
      SELECT sum(item.value*query_vector[item.ordinality::integer]) AS value
      FROM unnest(v.vector) WITH ORDINALITY item(value,ordinality)
    ) score
    WHERE score.value>=0.35
  ), ranked AS MATERIALIZED (
    SELECT * FROM candidates ORDER BY score DESC,node_id LIMIT result_limit
  )
  SELECT jsonb_build_object('id',r.node_id,'document_id',r.id,'title',d.title,
    'revision',d.source_version,'original_sha256',d.original_sha256,'media_type',d.media_type,
    'locator',r.locator,'text',r.text,'score',r.score,'source_segments',r.source_segments,
    'page_coverage',d.manifest#>'{documents,0,metadata,pages}',
    'extraction_complete',CASE WHEN d.media_type='application/pdf'
      THEN coalesce((d.manifest#>>'{documents,0,metadata,complete}')::boolean,false) ELSE true END,
    'relation','heuristic_semantic_similarity','authority_granted',false)
  FROM ranked r JOIN public.documents d ON d.id=r.id ORDER BY r.score DESC,r.node_id;
END $$;
REVOKE ALL ON FUNCTION nsai_library_semantic_search(double precision[],text[],text,integer[],text,integer) FROM PUBLIC;

