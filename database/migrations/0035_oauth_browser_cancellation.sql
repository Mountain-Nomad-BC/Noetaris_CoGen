-- A consumed OAuth state must not outlive a later browser logout. Lock the
-- browser epoch through login commit; logout invalidates pending callbacks and
-- all sessions from that browser, while preserving sessions on other devices.
CREATE TABLE oauth_browser_epochs (
 browser_hash text PRIMARY KEY CHECK(browser_hash ~ '^[a-f0-9]{64}$'),
 epoch bigint NOT NULL DEFAULT 1 CHECK(epoch>0),
 expires_at timestamptz NOT NULL DEFAULT clock_timestamp()+interval '24 hours'
);
ALTER TABLE oauth_browser_epochs ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON oauth_browser_epochs FROM PUBLIC;
ALTER TABLE oauth_login_sessions ADD COLUMN browser_hash text CHECK(browser_hash ~ '^[a-f0-9]{64}$');
CREATE INDEX oauth_sessions_browser ON oauth_login_sessions(browser_hash) WHERE revoked_at IS NULL;
CREATE INDEX oauth_pending_browser ON oauth_pending_states(browser_hash);

CREATE FUNCTION nsai_oauth_browser_epoch(p_browser text) RETURNS bigint
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE result bigint;
BEGIN
 IF public.nsai_actor()<>'legacy-service' OR public.nsai_actor_role()<>'service'
    OR nullif(current_setting('nsai.job_id',true),'') IS NOT NULL THEN
  RAISE EXCEPTION 'Authentication service only' USING ERRCODE='42501'; END IF;
 IF p_browser IS NULL OR p_browser !~ '^[a-f0-9]{64}$' THEN RAISE EXCEPTION 'Invalid browser binding'; END IF;
 PERFORM pg_advisory_xact_lock(878736);
 DELETE FROM public.oauth_browser_epochs b WHERE b.expires_at<=clock_timestamp()
  AND NOT EXISTS(SELECT 1 FROM public.oauth_login_sessions s WHERE s.browser_hash=b.browser_hash
                 AND s.revoked_at IS NULL AND s.expires_at>clock_timestamp());
 IF NOT EXISTS(SELECT 1 FROM public.oauth_browser_epochs WHERE browser_hash=p_browser)
    AND (SELECT count(*) FROM public.oauth_browser_epochs)>=10000 THEN
  RAISE EXCEPTION 'Authentication browser capacity exceeded'; END IF;
 INSERT INTO public.oauth_browser_epochs(browser_hash) VALUES(p_browser) ON CONFLICT DO NOTHING;
 SELECT epoch INTO result FROM public.oauth_browser_epochs WHERE browser_hash=p_browser FOR UPDATE;
 RETURN result;
END $$;

CREATE FUNCTION nsai_oauth_browser_assert(p_browser text,p_epoch bigint) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE current_epoch bigint;
BEGIN
 IF public.nsai_actor()<>'legacy-service' OR public.nsai_actor_role()<>'service'
    OR nullif(current_setting('nsai.job_id',true),'') IS NOT NULL THEN
  RAISE EXCEPTION 'Authentication service only' USING ERRCODE='42501'; END IF;
 SELECT epoch INTO current_epoch FROM public.oauth_browser_epochs WHERE browser_hash=p_browser FOR UPDATE;
 IF p_epoch IS NULL OR current_epoch IS NULL OR p_epoch<>current_epoch THEN
  RAISE EXCEPTION 'Browser authentication changed' USING ERRCODE='28000'; END IF;
 UPDATE public.oauth_browser_epochs SET expires_at=clock_timestamp()+interval '24 hours' WHERE browser_hash=p_browser;
END $$;

CREATE FUNCTION nsai_oauth_session_create(p_token text,p_csrf text,p_actor text,p_hours integer,p_browser text,p_epoch bigint) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
BEGIN
 PERFORM public.nsai_oauth_browser_assert(p_browser,p_epoch);
 PERFORM public.nsai_oauth_session_create(p_token,p_csrf,p_actor,p_hours);
 UPDATE public.oauth_login_sessions SET browser_hash=p_browser WHERE token_hash=p_token;
END $$;

CREATE FUNCTION nsai_oauth_browser_cancel(p_browser text) RETURNS integer
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE changed integer;
BEGIN
 -- Shared lock order: global epoch admission, then browser row, then sessions.
 PERFORM public.nsai_oauth_browser_epoch(p_browser);
 UPDATE public.oauth_browser_epochs SET epoch=epoch+1,expires_at=clock_timestamp()+interval '24 hours' WHERE browser_hash=p_browser;
 DELETE FROM public.oauth_pending_states WHERE browser_hash=p_browser;
 WITH revoked AS (
  UPDATE public.oauth_login_sessions SET revoked_at=clock_timestamp()
  WHERE browser_hash=p_browser AND revoked_at IS NULL RETURNING actor
 ) INSERT INTO public.oauth_identity_events(actor,event) SELECT actor,'session-revoked' FROM revoked;
 GET DIAGNOSTICS changed=ROW_COUNT;
 RETURN changed;
END $$;
REVOKE ALL ON FUNCTION nsai_oauth_browser_epoch(text),nsai_oauth_browser_assert(text,bigint),
 nsai_oauth_session_create(text,text,text,integer,text,bigint),nsai_oauth_browser_cancel(text) FROM PUBLIC;
