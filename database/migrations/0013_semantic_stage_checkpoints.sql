-- Transient checkpoints are private operational state, not accepted knowledge.
-- They survive retry/takeover and are removed atomically only after publication.
CREATE TABLE semantic_job_vectors (
  job_id text NOT NULL REFERENCES semantic_jobs(id),
  node_id text NOT NULL CHECK(node_id ~ '^[a-f0-9]{64}$'),
  vector jsonb NOT NULL CHECK(jsonb_typeof(vector)='array' AND jsonb_array_length(vector)=384),
  coverage jsonb NOT NULL CHECK(jsonb_typeof(coverage)='object'),
  artifact_sha256 text NOT NULL CHECK(artifact_sha256 ~ '^[a-f0-9]{64}$'),
  PRIMARY KEY(job_id,node_id)
);
CREATE FUNCTION nsai_checkpoint_lease(job_id text,token uuid) RETURNS public.semantic_jobs
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE job public.semantic_jobs;
BEGIN
  SELECT * INTO job FROM public.semantic_jobs WHERE id=job_id FOR SHARE;
  IF NOT FOUND OR job.state<>'running' OR job.lease_token IS DISTINCT FROM token
    OR job.requested_actor<>public.nsai_actor() OR job.id IS DISTINCT FROM current_setting('nsai.job_id',true)
    OR token::text IS DISTINCT FROM current_setting('nsai.job_lease',true)
    OR NOT public.nsai_job_source_allowed(job.document_id)
    THEN RAISE EXCEPTION 'Stale checkpoint lease' USING ERRCODE='40001'; END IF;
  RETURN job;
END $$;

CREATE FUNCTION nsai_put_semantic_checkpoints(job_id text,token uuid,records jsonb) RETURNS integer
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE job public.semantic_jobs; item jsonb; previous text; saved integer=0; norm double precision;
BEGIN
  job=public.nsai_checkpoint_lease(job_id,token);
  IF records IS NULL OR jsonb_typeof(records)<>'array' OR jsonb_array_length(records) NOT BETWEEN 1 AND 8
    OR octet_length(records::text)>1024*1024 THEN RAISE EXCEPTION 'Checkpoint batch budget exceeded'; END IF;
  IF (SELECT coalesce(sum(pg_column_size(vector)+pg_column_size(coverage)),0) FROM public.semantic_job_vectors WHERE semantic_job_vectors.job_id=job.id)
    +octet_length(records::text)>16*1024*1024 THEN RAISE EXCEPTION 'Checkpoint storage budget exceeded'; END IF;
  FOR item IN SELECT value FROM jsonb_array_elements(records) LOOP
    IF item->>'node_id' IS NULL OR item->>'node_id' !~ '^[a-f0-9]{64}$'
      OR jsonb_typeof(item->'vector') IS DISTINCT FROM 'array' OR jsonb_array_length(item->'vector')<>384
      OR jsonb_typeof(item->'coverage') IS DISTINCT FROM 'object'
      OR item->'coverage'->'complete' IS DISTINCT FROM 'true'::jsonb
      OR (item->'coverage'->>'input_tokens') IS NULL
      OR (item->'coverage'->>'input_tokens')::integer NOT BETWEEN 1 AND 32768
      OR item->'coverage'->>'covered_tokens' IS DISTINCT FROM item->'coverage'->>'input_tokens'
      OR item->'coverage'->>'max_sequence_length' IS DISTINCT FROM '256'
      OR item->'coverage'->>'pooling' IS DISTINCT FROM 'token-mean-overlap-compensated-special-mean'
      OR item->>'artifact_sha256' IS NULL OR item->>'artifact_sha256' !~ '^[a-f0-9]{64}$'
      OR EXISTS(SELECT 1 FROM jsonb_array_elements(item->'vector') value WHERE jsonb_typeof(value)<>'number')
      OR NOT EXISTS(SELECT 1 FROM public.document_knowledge k,jsonb_array_elements(k.knowledge->'nodes') node
        WHERE k.document_id=job.document_id AND k.artifact_sha256=job.knowledge_sha256
          AND node->>'kind'='passage' AND node->>'id'=item->>'node_id')
      THEN RAISE EXCEPTION 'Invalid source-bound checkpoint'; END IF;
    SELECT sum((value::text)::double precision*(value::text)::double precision) INTO norm
      FROM jsonb_array_elements(item->'vector') value;
    IF norm IS NULL OR norm NOT BETWEEN 0.999 AND 1.001 THEN RAISE EXCEPTION 'Checkpoint vector is not normalized'; END IF;
    SELECT artifact_sha256 INTO previous FROM public.semantic_job_vectors
      WHERE semantic_job_vectors.job_id=job.id AND node_id=item->>'node_id';
    IF previous IS NOT NULL AND previous<>item->>'artifact_sha256'
      THEN RAISE EXCEPTION 'Checkpoint content changed'; END IF;
    INSERT INTO public.semantic_job_vectors(job_id,node_id,vector,coverage,artifact_sha256)
      VALUES(job.id,item->>'node_id',item->'vector',item->'coverage',item->>'artifact_sha256') ON CONFLICT DO NOTHING;
    saved=saved+1;
  END LOOP;
  RETURN saved;
END $$;

CREATE FUNCTION nsai_get_semantic_checkpoints(job_id text,token uuid) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE job public.semantic_jobs;
BEGIN
  job=public.nsai_checkpoint_lease(job_id,token);
  RETURN coalesce((SELECT jsonb_object_agg(node_id,jsonb_build_object('vector',vector,'coverage',coverage,
    'artifact_sha256',artifact_sha256)) FROM public.semantic_job_vectors WHERE semantic_job_vectors.job_id=job.id),'{}'::jsonb);
END $$;

CREATE OR REPLACE FUNCTION nsai_clear_semantic_checkpoints(job_id text) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
BEGIN
  DELETE FROM public.semantic_job_vectors WHERE semantic_job_vectors.job_id=nsai_clear_semantic_checkpoints.job_id;
END $$;

CREATE FUNCTION nsai_retry_semantic_job(doc text,expected_epoch bigint) RETURNS text
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE job public.semantic_jobs; state_row public.source_index_state; target_job text;
BEGIN
  IF coalesce(current_setting('nsai.job_id',true),'')<>'' OR
    NOT EXISTS(SELECT 1 FROM public.document_owners WHERE document_id=doc AND owner_actor=public.nsai_actor())
    THEN RAISE EXCEPTION 'Source unavailable' USING ERRCODE='42501'; END IF;
  SELECT pending_job_id INTO target_job FROM public.source_index_state WHERE document_id=doc;
  SELECT * INTO job FROM public.semantic_jobs WHERE id=target_job FOR UPDATE;
  SELECT * INTO state_row FROM public.source_index_state WHERE document_id=doc FOR UPDATE;
  IF NOT FOUND OR state_row.epoch<>expected_epoch OR state_row.pending_job_id IS DISTINCT FROM job.id
    THEN RAISE EXCEPTION 'Stale index state' USING ERRCODE='40001'; END IF;
  IF job.state IS DISTINCT FROM 'failed' THEN RAISE EXCEPTION 'Only failed indexing can be retried'; END IF;
  UPDATE public.semantic_jobs SET state='queued',attempts=0,available_at=clock_timestamp(),error_code=NULL WHERE id=job.id;
  UPDATE public.source_index_state SET state='queued',epoch=epoch+1 WHERE document_id=doc;
  INSERT INTO public.semantic_job_events(job_id,event_type,attempt) VALUES(job.id,'requeued',0);
  RETURN job.id;
END $$;
REVOKE ALL ON FUNCTION nsai_checkpoint_lease(text,uuid),nsai_put_semantic_checkpoints(text,uuid,jsonb),
  nsai_get_semantic_checkpoints(text,uuid),nsai_retry_semantic_job(text,bigint) FROM PUBLIC;
