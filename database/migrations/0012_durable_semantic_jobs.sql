-- Durable orchestration owns DB credentials. Parser/encoder services receive
-- only bounded source payloads and their own service token, never DB secrets.
CREATE TABLE semantic_jobs (
  id text PRIMARY KEY CHECK(id ~ '^[a-f0-9]{64}$'),
  document_id text NOT NULL REFERENCES documents(id),
  requested_actor text NOT NULL,
  source_revision text NOT NULL,
  source_sha256 text NOT NULL CHECK(source_sha256 ~ '^[a-f0-9]{64}$'),
  knowledge_sha256 text NOT NULL CHECK(knowledge_sha256 ~ '^[a-f0-9]{64}$'),
  model_sha256 text NOT NULL CHECK(model_sha256 ~ '^[a-f0-9]{64}$'),
  state text NOT NULL DEFAULT 'queued' CHECK(state IN ('queued','running','succeeded','failed','cancelled')),
  attempts integer NOT NULL DEFAULT 0 CHECK(attempts BETWEEN 0 AND 3),
  lease_token uuid,
  lease_expires_at timestamptz,
  claimed_policy_epoch bigint,
  available_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  last_claimed_at timestamptz,
  error_code text,
  created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  UNIQUE(document_id,knowledge_sha256,model_sha256),
  CHECK((state='running')=(lease_token IS NOT NULL AND lease_expires_at IS NOT NULL))
);
CREATE INDEX semantic_jobs_queue ON semantic_jobs(model_sha256,state,available_at,created_at);
CREATE TABLE semantic_publications (
  id text PRIMARY KEY REFERENCES semantic_jobs(id),
  document_id text NOT NULL REFERENCES documents(id),
  model_sha256 text NOT NULL,
  knowledge_sha256 text NOT NULL,
  embedding_sha256 text NOT NULL,
  source_ids text[] NOT NULL,
  published_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE TRIGGER semantic_publications_immutable BEFORE UPDATE OR DELETE ON semantic_publications
  FOR EACH ROW EXECUTE FUNCTION nsai_refuse_update_delete();
CREATE TABLE source_index_state (
  document_id text PRIMARY KEY REFERENCES documents(id),
  current_publication_id text REFERENCES semantic_publications(id),
  pending_job_id text REFERENCES semantic_jobs(id),
  state text NOT NULL CHECK(state IN ('queued','running','ready','failed')),
  epoch bigint NOT NULL DEFAULT 1 CHECK(epoch>0)
);
CREATE TABLE semantic_job_events (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  job_id text NOT NULL REFERENCES semantic_jobs(id),
  event_type text NOT NULL CHECK(event_type IN ('queued','claimed','requeued','failed','published','cancelled')),
  attempt integer NOT NULL,
  error_code text,
  created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE TRIGGER semantic_job_events_immutable BEFORE UPDATE OR DELETE ON semantic_job_events
  FOR EACH ROW EXECUTE FUNCTION nsai_refuse_update_delete();
CREATE FUNCTION nsai_clear_semantic_checkpoints(job_id text) RETURNS void LANGUAGE plpgsql AS $$
BEGIN RETURN; END $$;
REVOKE ALL ON FUNCTION nsai_clear_semantic_checkpoints(text) FROM PUBLIC;

CREATE FUNCTION nsai_enqueue_semantic_job(job_id text,doc text,model_sha text,knowledge_sha text)
RETURNS text LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE inserted_id text; actor_id text; src public.documents;
BEGIN
  SELECT * INTO src FROM public.documents WHERE id=doc;
  IF NOT FOUND OR NOT public.nsai_document_visible(doc) OR
    NOT ((src.owner_scope=public.nsai_actor() AND public.nsai_actor_role()='operator') OR
      (src.owner_scope='legacy-shared' AND public.nsai_legacy_context()))
    OR coalesce(current_setting('nsai.job_id',true),'')<>''
    THEN RAISE EXCEPTION 'Source unavailable' USING ERRCODE='42501'; END IF;
  IF NOT EXISTS(SELECT 1 FROM public.document_knowledge WHERE document_id=doc AND artifact_sha256=knowledge_sha)
    THEN RAISE EXCEPTION 'Knowledge generation mismatch'; END IF;
  actor_id=CASE WHEN src.owner_scope='legacy-shared' THEN 'legacy-service' ELSE public.nsai_actor() END;
  INSERT INTO public.semantic_jobs(id,document_id,requested_actor,source_revision,source_sha256,knowledge_sha256,model_sha256)
    VALUES(job_id,doc,actor_id,src.source_version,src.original_sha256,knowledge_sha,model_sha)
    ON CONFLICT(document_id,knowledge_sha256,model_sha256) DO NOTHING RETURNING id INTO inserted_id;
  IF inserted_id IS NULL THEN
    SELECT id INTO inserted_id FROM public.semantic_jobs
      WHERE document_id=doc AND knowledge_sha256=knowledge_sha AND model_sha256=model_sha;
    RETURN inserted_id;
  END IF;
  INSERT INTO public.source_index_state(document_id,pending_job_id,state) VALUES(doc,inserted_id,'queued')
    ON CONFLICT(document_id) DO UPDATE SET pending_job_id=EXCLUDED.pending_job_id,state='queued',epoch=source_index_state.epoch+1;
  INSERT INTO public.semantic_job_events(job_id,event_type,attempt) VALUES(inserted_id,'queued',0);
  RETURN inserted_id;
END $$;

CREATE FUNCTION nsai_claim_semantic_job(model_sha text,active_actors text[],max_running integer,lease_seconds integer)
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
              WHERE previous.requested_actor=j.requested_actor) NULLS FIRST,j.created_at,j.id
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

CREATE FUNCTION nsai_job_source_allowed(doc text) RETURNS boolean LANGUAGE sql VOLATILE
SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  SELECT coalesce(current_setting('nsai.job_id',true),'')='' OR EXISTS(
    SELECT 1 FROM public.semantic_jobs j WHERE j.id=current_setting('nsai.job_id',true)
      AND j.document_id=doc AND j.requested_actor=public.nsai_actor() AND j.state='running'
      AND j.lease_token::text=current_setting('nsai.job_lease',true) AND j.lease_expires_at>clock_timestamp()
      AND j.claimed_policy_epoch=coalesce((SELECT epoch FROM public.document_policy_versions WHERE document_id=doc),0));
$$;
CREATE OR REPLACE FUNCTION nsai_source_scope_allows(doc text) RETURNS boolean LANGUAGE sql VOLATILE
SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  SELECT public.nsai_job_source_allowed(doc);
$$;
DO $$ DECLARE tab text; BEGIN
  FOREACH tab IN ARRAY ARRAY['documents','claims','source_spans','chunks','document_knowledge',
    'knowledge_embeddings','research_supplements','governed_records'] LOOP
    EXECUTE format('CREATE POLICY bounded_source_job ON %I AS RESTRICTIVE FOR ALL USING(public.nsai_job_source_allowed(%I)) WITH CHECK(public.nsai_job_source_allowed(%I))',
      tab,CASE WHEN tab='documents' THEN 'id' ELSE 'document_id' END,CASE WHEN tab='documents' THEN 'id' ELSE 'document_id' END);
  END LOOP;
END $$;

CREATE FUNCTION nsai_publish_semantic_job(job_id text,token uuid,embedding_sha text,active_actors text[])
RETURNS text LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE job public.semantic_jobs; embedding public.knowledge_embeddings; sources text[];
BEGIN
  SELECT * INTO job FROM public.semantic_jobs WHERE id=job_id FOR UPDATE;
  IF NOT FOUND OR active_actors IS NULL OR cardinality(active_actors)>1000
    OR job.state<>'running' OR job.lease_token IS DISTINCT FROM token
    OR job.lease_expires_at<=clock_timestamp() OR job.requested_actor<>public.nsai_actor()
    OR job.id IS DISTINCT FROM current_setting('nsai.job_id',true)
    OR token::text IS DISTINCT FROM current_setting('nsai.job_lease',true)
    OR NOT public.nsai_job_source_allowed(job.document_id)
    OR NOT (job.requested_actor='legacy-service' OR job.requested_actor=ANY(active_actors))
    THEN RAISE EXCEPTION 'Stale or unauthorized job lease' USING ERRCODE='40001'; END IF;
  IF NOT EXISTS(SELECT 1 FROM public.documents d JOIN public.document_knowledge k ON k.document_id=d.id
    WHERE d.id=job.document_id AND d.source_version=job.source_revision AND d.original_sha256=job.source_sha256
      AND k.artifact_sha256=job.knowledge_sha256)
    THEN RAISE EXCEPTION 'Job source generation changed' USING ERRCODE='40001'; END IF;
  SELECT * INTO embedding FROM public.knowledge_embeddings WHERE document_id=job.document_id
    AND model_sha256=job.model_sha256 AND artifact_sha256=embedding_sha;
  IF NOT FOUND OR embedding.payload->>'source_sha256' IS DISTINCT FROM job.source_sha256
    OR embedding.payload->>'knowledge_sha256' IS DISTINCT FROM job.knowledge_sha256
    OR embedding.payload#>>'{model_identity,sha256}' IS DISTINCT FROM job.model_sha256
    OR NOT(job.document_id=ANY(embedding.source_ids))
    OR NOT public.nsai_sources_visible(embedding.source_ids,embedding.provenance_complete)
    THEN RAISE EXCEPTION 'Incomplete validated embedding generation'; END IF;
  UPDATE public.semantic_jobs SET state='succeeded',lease_token=NULL,lease_expires_at=NULL
    WHERE id=job.id AND lease_expires_at>clock_timestamp();
  IF NOT FOUND THEN RAISE EXCEPTION 'Expired publication lease' USING ERRCODE='40001'; END IF;
  INSERT INTO public.semantic_publications(id,document_id,model_sha256,knowledge_sha256,embedding_sha256,source_ids)
    VALUES(job.id,job.document_id,job.model_sha256,job.knowledge_sha256,embedding_sha,embedding.source_ids);
  UPDATE public.source_index_state SET current_publication_id=job.id,state='ready',epoch=epoch+1
    WHERE document_id=job.document_id AND pending_job_id=job.id;
  IF NOT FOUND THEN RAISE EXCEPTION 'Job replaced before publication' USING ERRCODE='40001'; END IF;
  INSERT INTO public.semantic_job_events(job_id,event_type,attempt) VALUES(job.id,'published',job.attempts);
  PERFORM public.nsai_clear_semantic_checkpoints(job.id);
  RETURN job.id;
END $$;

CREATE FUNCTION nsai_fail_semantic_job(job_id text,token uuid,code text) RETURNS boolean
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE job public.semantic_jobs;
BEGIN
  IF public.nsai_actor()<>'legacy-service' OR coalesce(current_setting('nsai.job_id',true),'')<>''
    THEN RAISE EXCEPTION 'Orchestrator context required' USING ERRCODE='42501'; END IF;
  IF code NOT IN ('encoder-unavailable','invalid-artifact','stale-lease','authorization-changed','cancelled','processing-failed')
    OR code IS NULL THEN RAISE EXCEPTION 'Invalid bounded error code'; END IF;
  UPDATE public.semantic_jobs SET state=CASE WHEN attempts>=3 THEN 'failed' ELSE 'queued' END,
    lease_token=NULL,lease_expires_at=NULL,error_code=code,available_at=clock_timestamp()+interval '5 seconds'
    WHERE id=job_id AND state='running' AND lease_token=token RETURNING * INTO job;
  IF NOT FOUND THEN RETURN false; END IF;
  UPDATE public.source_index_state SET state=CASE WHEN job.state='failed' THEN 'failed' ELSE 'queued' END,
    epoch=epoch+1 WHERE document_id=job.document_id AND pending_job_id=job.id;
  INSERT INTO public.semantic_job_events(job_id,event_type,attempt,error_code)
    VALUES(job.id,CASE WHEN job.state='failed' THEN 'failed' ELSE 'requeued' END,job.attempts,code);
  RETURN true;
END $$;

CREATE FUNCTION nsai_source_index_status(doc text) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
BEGIN
  IF NOT EXISTS(SELECT 1 FROM public.documents WHERE id=doc) OR NOT public.nsai_document_visible(doc)
    THEN RAISE EXCEPTION 'Source unavailable' USING ERRCODE='42501'; END IF;
  RETURN coalesce((SELECT jsonb_build_object('document_id',doc,'state',s.state,'epoch',s.epoch,
    'ready',s.current_publication_id IS NOT NULL,'publication_id',s.current_publication_id,
    'job_id',j.id,'attempts',j.attempts,'error_code',j.error_code)
    FROM public.source_index_state s LEFT JOIN public.semantic_jobs j ON j.id=s.pending_job_id WHERE s.document_id=doc),
    jsonb_build_object('document_id',doc,'state','not-commissioned','ready',false));
END $$;
REVOKE ALL ON FUNCTION nsai_enqueue_semantic_job(text,text,text,text),
  nsai_claim_semantic_job(text,text[],integer,integer),nsai_job_source_allowed(text),
  nsai_publish_semantic_job(text,uuid,text,text[]),nsai_fail_semantic_job(text,uuid,text),
  nsai_source_index_status(text) FROM PUBLIC;
