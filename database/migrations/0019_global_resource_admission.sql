-- Global resource decisions bypass row filtering without returning private counts.
CREATE FUNCTION nsai_capacity_limits() RETURNS bigint[] LANGUAGE plpgsql STABLE
SET search_path=pg_catalog,public AS $$
DECLARE profile text=coalesce(nullif(current_setting('nsai.capacity_profile',true),''),'default');
BEGIN
  IF profile='default' THEN RETURN ARRAY[100,2000,134217728]::bigint[];
  ELSIF profile='reference-1000' THEN RETURN ARRAY[1000,2000,536870912]::bigint[];
  ELSE RAISE EXCEPTION 'Invalid server capacity profile'; END IF;
END $$;
REVOKE ALL ON FUNCTION nsai_capacity_limits() FROM PUBLIC;

CREATE FUNCTION nsai_source_capacity_available(proposed_claims integer) RETURNS boolean
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE limits bigint[]=public.nsai_capacity_limits();
BEGIN
  IF proposed_claims IS NULL OR proposed_claims NOT BETWEEN 0 AND 2000 THEN RETURN false; END IF;
  PERFORM pg_advisory_xact_lock(878704);
  RETURN (SELECT count(*) FROM public.documents)<limits[1]
     AND (SELECT count(*) FROM public.claims)+proposed_claims<=limits[2];
END $$;
REVOKE ALL ON FUNCTION nsai_source_capacity_available(integer) FROM PUBLIC;

CREATE TABLE semantic_storage_usage (
  singleton boolean PRIMARY KEY DEFAULT true CHECK(singleton),
  canonical_bytes bigint NOT NULL CHECK(canonical_bytes>=0)
);
INSERT INTO semantic_storage_usage(singleton,canonical_bytes)
  SELECT true,coalesce(sum(octet_length(payload::text)),0) FROM knowledge_embeddings;

CREATE FUNCTION nsai_semantic_storage_account() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE previous_bytes bigint=0; next_bytes bigint=0; used bigint; limits bigint[];
BEGIN
  PERFORM pg_advisory_xact_lock(878712);
  IF TG_OP<>'INSERT' THEN previous_bytes=octet_length(OLD.payload::text); END IF;
  IF TG_OP<>'DELETE' THEN next_bytes=octet_length(NEW.payload::text); END IF;
  limits=public.nsai_capacity_limits();
  SELECT canonical_bytes INTO STRICT used FROM public.semantic_storage_usage WHERE singleton FOR UPDATE;
  IF next_bytes>previous_bytes AND used-previous_bytes+next_bytes>limits[3] THEN
    RAISE EXCEPTION 'Semantic artifact storage capacity reached' USING ERRCODE='54000'; END IF;
  UPDATE public.semantic_storage_usage SET canonical_bytes=used-previous_bytes+next_bytes WHERE singleton;
  IF TG_OP='DELETE' THEN RETURN OLD; END IF;
  RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION nsai_semantic_storage_account() FROM PUBLIC;
CREATE TRIGGER semantic_storage_account BEFORE INSERT OR UPDATE OR DELETE ON knowledge_embeddings
  FOR EACH ROW EXECUTE FUNCTION nsai_semantic_storage_account();

CREATE OR REPLACE FUNCTION nsai_fail_semantic_job(job_id text,token uuid,code text) RETURNS boolean
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE job public.semantic_jobs;
BEGIN
  IF public.nsai_actor()<>'legacy-service' OR coalesce(current_setting('nsai.job_id',true),'')<>''
    THEN RAISE EXCEPTION 'Orchestrator context required' USING ERRCODE='42501'; END IF;
  IF code NOT IN ('encoder-unavailable','invalid-artifact','stale-lease','authorization-changed','cancelled','processing-failed','capacity-exhausted')
    OR code IS NULL THEN RAISE EXCEPTION 'Invalid bounded error code'; END IF;
  UPDATE public.semantic_jobs SET state=CASE WHEN attempts>=3 OR code='capacity-exhausted' THEN 'failed' ELSE 'queued' END,
    lease_token=NULL,lease_expires_at=NULL,error_code=code,available_at=clock_timestamp()+interval '5 seconds'
    WHERE id=job_id AND state='running' AND lease_token=token RETURNING * INTO job;
  IF NOT FOUND THEN RETURN false; END IF;
  UPDATE public.source_index_state SET state=CASE WHEN job.state='failed' THEN 'failed' ELSE 'queued' END,
    epoch=epoch+1 WHERE document_id=job.document_id AND pending_job_id=job.id;
  INSERT INTO public.semantic_job_events(job_id,event_type,attempt,error_code)
    VALUES(job.id,CASE WHEN job.state='failed' THEN 'failed' ELSE 'requeued' END,job.attempts,code);
  RETURN true;
END $$;
