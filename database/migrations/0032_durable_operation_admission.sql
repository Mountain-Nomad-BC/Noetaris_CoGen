CREATE TABLE operation_admissions (
 id text PRIMARY KEY CHECK(id ~ '^[a-f0-9]{32}$'), actor text NOT NULL,
 kind text NOT NULL CHECK(kind IN ('generation','ingestion')),
 state text NOT NULL CHECK(state IN ('queued','active','finished','expired')),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 expires_at timestamptz NOT NULL, finished_at timestamptz
);
CREATE INDEX operation_live_queue ON operation_admissions(kind,created_at,id) WHERE state IN ('queued','active');
CREATE UNIQUE INDEX operation_one_identity ON operation_admissions(actor,kind,id);
ALTER TABLE operation_admissions ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON operation_admissions FROM PUBLIC;

CREATE FUNCTION nsai_operation_begin(p_id text,p_kind text,p_users integer,p_personal integer,p_global integer,p_queue integer)
RETURNS text LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE old public.operation_admissions%ROWTYPE; next_state text;
BEGIN
 IF public.nsai_actor_role()<>'operator' OR nullif(current_setting('nsai.job_id',true),'') IS NOT NULL THEN
  RAISE EXCEPTION 'Operation not permitted' USING ERRCODE='42501'; END IF;
 IF p_id IS NULL OR p_id !~ '^[a-f0-9]{32}$' OR p_kind IS NULL OR p_kind NOT IN ('generation','ingestion')
    OR p_users IS NULL OR p_users NOT BETWEEN 1 AND 1000 OR p_personal IS NULL OR p_personal NOT BETWEEN 1 AND 100
    OR p_global IS NULL OR p_global NOT BETWEEN 1 AND 1000 OR p_queue IS NULL OR p_queue NOT BETWEEN 0 AND 1000 THEN
  RAISE EXCEPTION 'Invalid operation admission'; END IF;
 PERFORM pg_advisory_xact_lock(878733);
 UPDATE public.operation_admissions SET state='expired',finished_at=clock_timestamp()
  WHERE state IN ('active','queued') AND expires_at<=clock_timestamp();
 SELECT * INTO old FROM public.operation_admissions WHERE id=p_id;
 IF FOUND THEN
  IF old.actor<>public.nsai_actor() OR old.kind<>p_kind THEN RAISE EXCEPTION 'Operation unavailable' USING ERRCODE='42501'; END IF;
  RETURN old.state;
 END IF;
 IF (SELECT count(*) FROM public.operation_admissions WHERE actor=public.nsai_actor() AND kind=p_kind AND state IN ('queued','active'))>=p_personal THEN
  RETURN 'personal-limit'; END IF;
 IF NOT EXISTS(SELECT 1 FROM public.operation_admissions WHERE actor=public.nsai_actor() AND state IN ('queued','active'))
    AND (SELECT count(DISTINCT actor) FROM public.operation_admissions WHERE state IN ('queued','active'))>=p_users THEN
  RETURN 'user-limit'; END IF;
 IF NOT EXISTS(SELECT 1 FROM public.operation_admissions WHERE kind=p_kind AND state='queued')
    AND (SELECT count(*) FROM public.operation_admissions WHERE kind=p_kind AND state='active')<p_global THEN
  next_state='active';
 ELSE
  IF (SELECT count(*) FROM public.operation_admissions WHERE kind=p_kind AND state='queued')>=p_queue THEN RETURN 'queue-limit'; END IF;
  next_state='queued';
 END IF;
 INSERT INTO public.operation_admissions(id,actor,kind,state,expires_at)
  VALUES(p_id,public.nsai_actor(),p_kind,next_state,clock_timestamp()+interval '10 minutes');
 RETURN next_state;
END $$;

CREATE FUNCTION nsai_operation_claim(p_id text,p_global integer) RETURNS text
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE old public.operation_admissions%ROWTYPE;
BEGIN
 IF p_global IS NULL OR p_global NOT BETWEEN 1 AND 1000 THEN RAISE EXCEPTION 'Invalid active operation bound'; END IF;
 IF public.nsai_actor_role()<>'operator' OR nullif(current_setting('nsai.job_id',true),'') IS NOT NULL THEN
  RAISE EXCEPTION 'Operation not permitted' USING ERRCODE='42501'; END IF;
 PERFORM pg_advisory_xact_lock(878733);
 UPDATE public.operation_admissions SET state='expired',finished_at=clock_timestamp()
  WHERE state IN ('active','queued') AND expires_at<=clock_timestamp();
 SELECT * INTO old FROM public.operation_admissions WHERE id=p_id;
 IF NOT FOUND OR old.actor<>public.nsai_actor() THEN RAISE EXCEPTION 'Operation unavailable' USING ERRCODE='42501'; END IF;
 IF old.state<>'queued' THEN RETURN old.state; END IF;
 IF (SELECT count(*) FROM public.operation_admissions WHERE kind=old.kind AND state='active')<p_global
    AND p_id=(SELECT id FROM public.operation_admissions WHERE kind=old.kind AND state='queued' ORDER BY created_at,id LIMIT 1) THEN
  UPDATE public.operation_admissions SET state='active',expires_at=clock_timestamp()+interval '10 minutes' WHERE id=p_id;
  RETURN 'active';
 END IF;
 RETURN 'queued';
END $$;

CREATE FUNCTION nsai_operation_finish(p_id text) RETURNS boolean
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
BEGIN
 IF public.nsai_actor_role()<>'operator' OR nullif(current_setting('nsai.job_id',true),'') IS NOT NULL THEN
  RAISE EXCEPTION 'Operation not permitted' USING ERRCODE='42501'; END IF;
 PERFORM pg_advisory_xact_lock(878733);
 UPDATE public.operation_admissions SET state='finished',finished_at=clock_timestamp()
  WHERE id=p_id AND actor=public.nsai_actor() AND state IN ('active','queued');
 RETURN FOUND;
END $$;
REVOKE ALL ON FUNCTION nsai_operation_begin(text,text,integer,integer,integer,integer),
 nsai_operation_claim(text,integer),nsai_operation_finish(text) FROM PUBLIC;
