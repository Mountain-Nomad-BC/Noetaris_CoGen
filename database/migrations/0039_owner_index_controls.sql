-- Owner controls: cancellation never deletes original bytes, vectors or publications.
ALTER TABLE semantic_jobs ADD COLUMN priority integer NOT NULL DEFAULT 0 CHECK(priority BETWEEN 0 AND 9);
ALTER TABLE semantic_job_events ADD COLUMN control_details jsonb NOT NULL DEFAULT'{}'::jsonb CHECK(jsonb_typeof(control_details)='object');
ALTER TABLE semantic_job_events DROP CONSTRAINT semantic_job_events_event_type_check;
ALTER TABLE semantic_job_events ADD CONSTRAINT semantic_job_events_event_type_check CHECK(event_type IN('queued','claimed','requeued','failed','published','cancelled','priority-changed'));
ALTER TABLE source_index_state DROP CONSTRAINT source_index_state_state_check;
ALTER TABLE source_index_state ADD CONSTRAINT source_index_state_state_check CHECK(state IN('queued','running','ready','failed','cancelled'));
CREATE FUNCTION nsai_cancel_semantic_job(doc text,expected_epoch bigint) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE job public.semantic_jobs; observed public.source_index_state; target text; next_epoch bigint;
BEGIN
 IF public.nsai_actor_role() IS DISTINCT FROM 'operator' OR coalesce(current_setting('nsai.job_id',true),'')<>'' OR NOT public.nsai_source_is_owner(doc)
 THEN RAISE EXCEPTION 'Source unavailable' USING ERRCODE='42501'; END IF;
 SELECT pending_job_id INTO target FROM public.source_index_state WHERE document_id=doc;
 SELECT * INTO job FROM public.semantic_jobs WHERE id=target FOR UPDATE;
 SELECT * INTO observed FROM public.source_index_state WHERE document_id=doc FOR UPDATE;
 IF NOT FOUND OR job.id IS NULL OR expected_epoch IS NULL OR expected_epoch<1 OR observed.epoch<>expected_epoch OR observed.pending_job_id IS DISTINCT FROM job.id
 THEN RAISE EXCEPTION 'Stale index state' USING ERRCODE='40001'; END IF;
 IF job.requested_actor IS DISTINCT FROM public.nsai_actor() THEN RAISE EXCEPTION 'Source unavailable' USING ERRCODE='42501'; END IF;
 IF job.state NOT IN('queued','running') THEN RAISE EXCEPTION 'Only pending indexing can be cancelled' USING ERRCODE='40001'; END IF;
 UPDATE public.semantic_jobs SET state='cancelled',lease_token=NULL,lease_expires_at=NULL,error_code='cancelled' WHERE id=job.id;
 UPDATE public.source_index_state SET state=CASE WHEN current_publication_id IS NULL THEN 'cancelled' ELSE 'ready' END,epoch=epoch+1 WHERE document_id=doc RETURNING epoch INTO next_epoch;
 INSERT INTO public.semantic_job_events(job_id,event_type,attempt,control_details) VALUES(job.id,'cancelled',job.attempts,jsonb_build_object('actor',public.nsai_actor(),'expected_epoch',expected_epoch,'epoch',next_epoch,'previous_state',job.state));
 RETURN jsonb_build_object('job_id',job.id,'state','cancelled','epoch',next_epoch,'index_state',CASE WHEN observed.current_publication_id IS NULL THEN 'cancelled' ELSE 'ready' END);
END $$;
CREATE FUNCTION nsai_set_semantic_job_priority(doc text,expected_epoch bigint,requested_priority integer) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE job public.semantic_jobs; observed public.source_index_state; target text; next_epoch bigint;
BEGIN
 IF public.nsai_actor_role() IS DISTINCT FROM 'operator' OR coalesce(current_setting('nsai.job_id',true),'')<>'' OR NOT public.nsai_source_is_owner(doc)
 THEN RAISE EXCEPTION 'Source unavailable' USING ERRCODE='42501'; END IF;
 SELECT pending_job_id INTO target FROM public.source_index_state WHERE document_id=doc;
 SELECT * INTO job FROM public.semantic_jobs WHERE id=target FOR UPDATE;
 SELECT * INTO observed FROM public.source_index_state WHERE document_id=doc FOR UPDATE;
 IF NOT FOUND OR job.id IS NULL OR expected_epoch IS NULL OR expected_epoch<1 OR observed.epoch<>expected_epoch OR observed.pending_job_id IS DISTINCT FROM job.id
 THEN RAISE EXCEPTION 'Stale index state' USING ERRCODE='40001'; END IF;
 IF job.requested_actor IS DISTINCT FROM public.nsai_actor() THEN RAISE EXCEPTION 'Source unavailable' USING ERRCODE='42501'; END IF;
 IF requested_priority IS NULL OR requested_priority NOT BETWEEN 0 AND 9 THEN RAISE EXCEPTION 'Priority must be an integer from 0 through 9' USING ERRCODE='22023'; END IF;
 IF job.state<>'queued' THEN RAISE EXCEPTION 'Only queued indexing can change priority' USING ERRCODE='40001'; END IF;
 UPDATE public.semantic_jobs SET priority=requested_priority WHERE id=job.id;
 UPDATE public.source_index_state SET epoch=epoch+1 WHERE document_id=doc RETURNING epoch INTO next_epoch;
 INSERT INTO public.semantic_job_events(job_id,event_type,attempt,control_details) VALUES(job.id,'priority-changed',job.attempts,jsonb_build_object('actor',public.nsai_actor(),'expected_epoch',expected_epoch,'epoch',next_epoch,'previous_priority',job.priority,'priority',requested_priority));
 RETURN jsonb_build_object('job_id',job.id,'state','queued','priority',requested_priority,'epoch',next_epoch);
END $$;
CREATE OR REPLACE FUNCTION nsai_retry_semantic_job(doc text,expected_epoch bigint) RETURNS text
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE job public.semantic_jobs; state_row public.source_index_state; target_job text;
BEGIN
  IF public.nsai_actor_role() IS DISTINCT FROM 'operator' OR coalesce(current_setting('nsai.job_id',true),'')<>'' OR
    NOT EXISTS(SELECT 1 FROM public.document_owners WHERE document_id=doc AND owner_actor=public.nsai_actor())
    THEN RAISE EXCEPTION 'Source unavailable' USING ERRCODE='42501'; END IF;
  SELECT pending_job_id INTO target_job FROM public.source_index_state WHERE document_id=doc;
  SELECT * INTO job FROM public.semantic_jobs WHERE id=target_job FOR UPDATE;
  SELECT * INTO state_row FROM public.source_index_state WHERE document_id=doc FOR UPDATE;
  IF NOT FOUND OR job.id IS NULL OR expected_epoch IS NULL OR expected_epoch<1 OR state_row.epoch<>expected_epoch OR state_row.pending_job_id IS DISTINCT FROM job.id
    THEN RAISE EXCEPTION 'Stale index state' USING ERRCODE='40001'; END IF;
  IF job.state NOT IN('failed','cancelled') THEN RAISE EXCEPTION 'Only failed or cancelled indexing can be retried' USING ERRCODE='40001'; END IF;
  UPDATE public.semantic_jobs SET state='queued',attempts=0,available_at=clock_timestamp(),error_code=NULL WHERE id=job.id;
  UPDATE public.source_index_state SET state='queued',epoch=epoch+1 WHERE document_id=doc;
  INSERT INTO public.semantic_job_events(job_id,event_type,attempt,control_details) VALUES(job.id,'requeued',0,jsonb_build_object('actor',public.nsai_actor(),'expected_epoch',expected_epoch,'epoch',state_row.epoch+1,'previous_state',job.state));
  RETURN job.id;
END $$;
CREATE OR REPLACE FUNCTION nsai_claim_semantic_job(model_sha text,active_actors text[],max_running integer,lease_seconds integer)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE job public.semantic_jobs; expired public.semantic_jobs; token uuid; policy_epoch bigint;
BEGIN
  IF public.nsai_actor()<>'legacy-service' OR coalesce(current_setting('nsai.job_id',true),'')<>''
    THEN RAISE EXCEPTION 'Orchestrator context required' USING ERRCODE='42501'; END IF;
  IF model_sha IS NULL OR model_sha !~ '^[a-f0-9]{64}$' OR active_actors IS NULL OR cardinality(active_actors)>1000
    OR max_running IS NULL OR lease_seconds IS NULL
    OR max_running NOT BETWEEN 1 AND 2 OR lease_seconds NOT BETWEEN 30 AND 300
    THEN RAISE EXCEPTION 'Invalid bounded job admission'; END IF;
  PERFORM pg_advisory_xact_lock(878720);
  FOR expired IN UPDATE public.semantic_jobs SET
    state=CASE WHEN attempts>=3 THEN 'failed' ELSE 'queued' END,
    lease_token=NULL,lease_expires_at=NULL,available_at=clock_timestamp(),error_code='stale-lease'
    WHERE state='running' AND lease_expires_at<=clock_timestamp() RETURNING * LOOP
      INSERT INTO public.semantic_job_events(job_id,event_type,attempt,error_code)
        VALUES(expired.id,CASE WHEN expired.state='failed' THEN 'failed' ELSE 'requeued' END,expired.attempts,'stale-lease');
      UPDATE public.source_index_state SET state=CASE WHEN expired.state='failed' THEN 'failed' ELSE 'queued' END,
        epoch=epoch+1 WHERE document_id=expired.document_id AND pending_job_id=expired.id;
  END LOOP;
  IF (SELECT count(*) FROM public.semantic_jobs WHERE state='running')>=max_running THEN RETURN NULL; END IF;
  SELECT j.* INTO job FROM public.semantic_jobs j
    JOIN public.documents d ON d.id=j.document_id
    JOIN public.document_knowledge k ON k.document_id=j.document_id
    WHERE j.state='queued' AND j.attempts<3 AND j.available_at<=clock_timestamp() AND j.model_sha256=model_sha
      AND (j.requested_actor='legacy-service' OR j.requested_actor=ANY(active_actors))
      AND d.source_version=j.source_revision AND d.original_sha256=j.source_sha256 AND k.artifact_sha256=j.knowledge_sha256
      AND ((j.requested_actor='legacy-service' AND d.owner_scope='legacy-shared') OR d.owner_scope=j.requested_actor)
    ORDER BY (SELECT max(previous.last_claimed_at) FROM public.semantic_jobs previous
              WHERE previous.requested_actor=j.requested_actor) NULLS FIRST,j.priority DESC,j.created_at,j.id
    LIMIT 1 FOR UPDATE OF j SKIP LOCKED;
  IF NOT FOUND THEN RETURN NULL; END IF;
  SELECT coalesce((SELECT epoch FROM public.document_policy_versions WHERE document_id=job.document_id),0) INTO policy_epoch;
  token=gen_random_uuid();
  UPDATE public.semantic_jobs SET state='running',attempts=attempts+1,lease_token=token,
    lease_expires_at=clock_timestamp()+make_interval(secs=>lease_seconds),last_claimed_at=clock_timestamp(),
    claimed_policy_epoch=policy_epoch,error_code=NULL WHERE id=job.id RETURNING * INTO job;
  UPDATE public.source_index_state SET state='running',epoch=epoch+1 WHERE document_id=job.document_id AND pending_job_id=job.id;
  INSERT INTO public.semantic_job_events(job_id,event_type,attempt) VALUES(job.id,'claimed',job.attempts);
  RETURN jsonb_build_object('id',job.id,'document_id',job.document_id,'actor',job.requested_actor,
    'source_revision',job.source_revision,'source_sha256',job.source_sha256,'knowledge_sha256',job.knowledge_sha256,
    'model_sha256',job.model_sha256,'attempt',job.attempts,'lease_token',token,'lease_expires_at',job.lease_expires_at);
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
    'job_id',j.id,'job_state',j.state,'priority',j.priority,'attempts',j.attempts,'error_code',j.error_code,'passages_total',total_passages,
    'source_coverage_complete',coverage_complete,
    'passages_completed',CASE WHEN total_passages IS NULL THEN NULL WHEN j.state='succeeded' THEN total_passages ELSE
      (SELECT count(*) FROM public.semantic_job_vectors v WHERE v.job_id=j.id) END)
    FROM public.source_index_state s LEFT JOIN public.semantic_jobs j ON j.id=s.pending_job_id WHERE s.document_id=doc),
    jsonb_build_object('document_id',doc,'state','not-commissioned','ready',false));
END $$;
REVOKE ALL ON FUNCTION nsai_cancel_semantic_job(text,bigint),nsai_set_semantic_job_priority(text,bigint,integer) FROM PUBLIC;
