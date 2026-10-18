-- Short-lived authentication state shares NSAI's authoritative database.
-- This adds no content privileges and changes no existing identity or owner.
CREATE TABLE oauth_pending_states (
 state_hash text PRIMARY KEY CHECK(state_hash ~ '^[a-f0-9]{64}$'),
 browser_hash text NOT NULL CHECK(browser_hash ~ '^[a-f0-9]{64}$'),
 payload text NOT NULL CHECK(octet_length(payload) BETWEEN 1 AND 8192),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 expires_at timestamptz NOT NULL DEFAULT clock_timestamp()+interval '5 minutes'
);
CREATE INDEX oauth_pending_expiry ON oauth_pending_states(expires_at);
ALTER TABLE oauth_pending_states ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON oauth_pending_states FROM PUBLIC;

CREATE FUNCTION nsai_oauth_state_put(p_state text,p_browser text,p_payload text) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
BEGIN
 IF public.nsai_actor()<>'legacy-service' OR public.nsai_actor_role()<>'service'
    OR nullif(current_setting('nsai.job_id',true),'') IS NOT NULL THEN
  RAISE EXCEPTION 'Authentication service only' USING ERRCODE='42501'; END IF;
 IF p_state IS NULL OR p_state !~ '^[a-f0-9]{64}$' OR p_browser IS NULL OR p_browser !~ '^[a-f0-9]{64}$'
    OR p_payload IS NULL OR octet_length(p_payload) NOT BETWEEN 1 AND 8192 THEN
  RAISE EXCEPTION 'Invalid authentication state'; END IF;
 PERFORM pg_advisory_xact_lock(878734);
 DELETE FROM public.oauth_pending_states WHERE expires_at<=clock_timestamp();
 IF (SELECT count(*) FROM public.oauth_pending_states)>=10000
    OR (SELECT count(*) FROM public.oauth_pending_states WHERE browser_hash=p_browser)>=8 THEN
  RAISE EXCEPTION 'Authentication state capacity exceeded'; END IF;
 INSERT INTO public.oauth_pending_states(state_hash,browser_hash,payload) VALUES(p_state,p_browser,p_payload);
END $$;

CREATE FUNCTION nsai_oauth_state_take(p_state text,p_browser text) RETURNS text
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE result text;
BEGIN
 IF public.nsai_actor()<>'legacy-service' OR public.nsai_actor_role()<>'service'
    OR nullif(current_setting('nsai.job_id',true),'') IS NOT NULL THEN
  RAISE EXCEPTION 'Authentication service only' USING ERRCODE='42501'; END IF;
 -- DELETE RETURNING is a single atomic consumption, including across workers.
 DELETE FROM public.oauth_pending_states WHERE state_hash=p_state AND browser_hash=p_browser
  AND expires_at>clock_timestamp() RETURNING payload INTO result;
 RETURN result;
END $$;

CREATE FUNCTION nsai_oauth_state_clear(p_state text,p_browser text) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
BEGIN
 IF public.nsai_actor()<>'legacy-service' OR public.nsai_actor_role()<>'service'
    OR nullif(current_setting('nsai.job_id',true),'') IS NOT NULL THEN
  RAISE EXCEPTION 'Authentication service only' USING ERRCODE='42501'; END IF;
 DELETE FROM public.oauth_pending_states WHERE state_hash=p_state AND browser_hash=p_browser;
END $$;
REVOKE ALL ON FUNCTION nsai_oauth_state_put(text,text,text),nsai_oauth_state_take(text,text),
 nsai_oauth_state_clear(text,text) FROM PUBLIC;
