-- Native double arrays are an immutable derived index of canonical JSON vectors.
-- No approximate search, quantization or new external extension is introduced.
CREATE FUNCTION nsai_native_vector_valid(vector double precision[]) RETURNS boolean
LANGUAGE plpgsql IMMUTABLE SET search_path=pg_catalog,public AS $$
DECLARE norm double precision;
BEGIN
  IF vector IS NULL OR array_ndims(vector)<>1 OR array_lower(vector,1)<>1 OR cardinality(vector)<>384
    OR EXISTS(SELECT 1 FROM unnest(vector) v WHERE v IS NULL OR v::text IN ('NaN','Infinity','-Infinity')) THEN RETURN false; END IF;
  BEGIN
    SELECT sum(v*v) INTO norm FROM unnest(vector) v;
    RETURN abs(norm-1)<=0.00002;
  EXCEPTION WHEN numeric_value_out_of_range THEN RETURN false;
  END;
END $$;
REVOKE ALL ON FUNCTION nsai_native_vector_valid(double precision[]) FROM PUBLIC;

CREATE TABLE native_semantic_passages (
  document_id text NOT NULL,
  model_sha256 text NOT NULL CHECK(model_sha256='6fd5d72fe4589f189f8ebc006442dbb529bb7ce38f8082112682524616046452'),
  embedding_sha256 text NOT NULL CHECK(embedding_sha256 ~ '^[a-f0-9]{64}$'),
  node_id text NOT NULL CHECK(node_id ~ '^[a-f0-9]{64}$'),
  locator text NOT NULL CHECK(length(locator) BETWEEN 1 AND 200),
  page integer CHECK(page BETWEEN 1 AND 1000),
  text text NOT NULL CHECK(octet_length(text) BETWEEN 1 AND 64000),
  source_segments jsonb NOT NULL CHECK(jsonb_typeof(source_segments)='array'),
  vector double precision[] NOT NULL CHECK(public.nsai_native_vector_valid(vector)),
  source_ids text[] NOT NULL,
  provenance_complete boolean NOT NULL CHECK(provenance_complete),
  PRIMARY KEY(document_id,model_sha256,embedding_sha256,node_id),
  FOREIGN KEY(document_id,model_sha256) REFERENCES knowledge_embeddings(document_id,model_sha256),
  CHECK(cardinality(source_ids) BETWEEN 1 AND 1000 AND array_position(source_ids,NULL) IS NULL AND document_id=ANY(source_ids))
);
ALTER TABLE native_semantic_passages ALTER COLUMN vector SET STORAGE PLAIN;
ALTER TABLE native_semantic_passages ENABLE ROW LEVEL SECURITY;
CREATE POLICY native_passage_read ON native_semantic_passages FOR SELECT USING
  (public.nsai_document_visible(document_id) AND public.nsai_sources_visible(source_ids,provenance_complete));
CREATE TRIGGER native_passages_immutable BEFORE UPDATE OR DELETE ON native_semantic_passages
  FOR EACH ROW EXECUTE FUNCTION reject_evidence_mutation();

CREATE FUNCTION nsai_build_native_passages(doc text,model text) RETURNS integer
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE parent public.knowledge_embeddings; nodes jsonb; node jsonb; node_key text;
  vectors jsonb; coordinates double precision[]; expected integer; observed integer=0;
BEGIN
  IF model<>'6fd5d72fe4589f189f8ebc006442dbb529bb7ce38f8082112682524616046452' THEN RETURN 0; END IF;
  SELECT * INTO STRICT parent FROM public.knowledge_embeddings WHERE document_id=doc AND model_sha256=model;
  IF NOT parent.provenance_complete THEN RETURN 0; END IF;
  SELECT coalesce(knowledge->'nodes','[]'::jsonb) INTO STRICT nodes FROM public.document_knowledge WHERE document_id=doc;
  vectors=coalesce(parent.payload->'vectors','{}'::jsonb);
  IF jsonb_typeof(nodes)<>'array' OR jsonb_typeof(vectors)<>'object' THEN RAISE EXCEPTION 'Invalid native passage inventory'; END IF;
  SELECT count(*) INTO expected FROM jsonb_array_elements(nodes) n WHERE n->>'kind'='passage';
  IF expected>10000 OR (SELECT count(*) FROM jsonb_object_keys(vectors))<>expected THEN
    RAISE EXCEPTION 'Incomplete native passage inventory'; END IF;
  FOR node IN SELECT value FROM jsonb_array_elements(nodes) WHERE value->>'kind'='passage' LOOP
    node_key=node->>'id';
    IF node_key IS NULL OR jsonb_typeof(vectors->node_key) IS DISTINCT FROM 'array'
      OR jsonb_array_length(vectors->node_key)<>384
      OR EXISTS(SELECT 1 FROM jsonb_array_elements(vectors->node_key) v WHERE jsonb_typeof(v)<>'number') THEN
      RAISE EXCEPTION 'Invalid native passage vector'; END IF;
    SELECT array_agg(value::double precision ORDER BY ordinality) INTO coordinates
      FROM jsonb_array_elements_text(vectors->node_key) WITH ORDINALITY v(value,ordinality);
    INSERT INTO public.native_semantic_passages(document_id,model_sha256,embedding_sha256,node_id,locator,page,text,source_segments,vector,source_ids,provenance_complete)
      VALUES(doc,model,parent.artifact_sha256,node_key,node->>'locator',(node->>'page')::integer,node->>'text',
        coalesce(node->'source_segments','[]'::jsonb),coordinates,parent.source_ids,true);
    observed=observed+1;
  END LOOP;
  RETURN observed;
END $$;
REVOKE ALL ON FUNCTION nsai_build_native_passages(text,text) FROM PUBLIC;
CREATE FUNCTION nsai_native_passage_insert() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
BEGIN
  PERFORM public.nsai_build_native_passages(NEW.document_id,NEW.model_sha256);
  RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION nsai_native_passage_insert() FROM PUBLIC;
CREATE TRIGGER native_passage_insert AFTER INSERT ON knowledge_embeddings
  FOR EACH ROW EXECUTE FUNCTION nsai_native_passage_insert();
DO $$ DECLARE item record; BEGIN
  FOR item IN SELECT document_id,model_sha256 FROM knowledge_embeddings
    WHERE model_sha256='6fd5d72fe4589f189f8ebc006442dbb529bb7ce38f8082112682524616046452' AND provenance_complete LOOP
    PERFORM public.nsai_build_native_passages(item.document_id,item.model_sha256);
  END LOOP;
END $$;

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
    FROM authorized a JOIN public.native_semantic_passages v
      ON v.document_id=a.id AND v.model_sha256=a.model_sha256 AND v.embedding_sha256=a.artifact_sha256
    CROSS JOIN LATERAL (
      SELECT sum(item.value*query_vector[item.ordinality::integer]) AS value
      FROM unnest(v.vector) WITH ORDINALITY item(value,ordinality)
    ) score
    WHERE (page_filter IS NULL OR v.page=ANY(page_filter))
      AND (entity_filter IS NULL OR to_tsvector('english',v.text) @@ websearch_to_tsquery('english',entity_filter))
      AND score.value>=0.35
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

