-- Canonical actor strings remain unchanged. Provider email/name never identify
-- an NSAI account and provider claims never assign NSAI roles.
CREATE TABLE oauth_accounts (
 actor text PRIMARY KEY CHECK(actor ~ '^local-user-[a-z][a-z0-9_-]{0,63}$'),
 authority text NOT NULL CHECK(authority IN ('registry','provider')),
 enabled boolean NOT NULL DEFAULT true,
 created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE TABLE oauth_bindings (
 provider text NOT NULL CHECK(provider IN ('google','github')),
 subject text NOT NULL CHECK(subject ~ '^[a-zA-Z0-9_-]{1,255}$'),
 actor text NOT NULL REFERENCES oauth_accounts(actor),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(provider,subject), UNIQUE(actor,provider)
);
CREATE TABLE oauth_login_sessions (
 token_hash text PRIMARY KEY CHECK(token_hash ~ '^[a-f0-9]{64}$'),
 csrf_hash text NOT NULL CHECK(csrf_hash ~ '^[a-f0-9]{64}$'),
 actor text NOT NULL REFERENCES oauth_accounts(actor),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 expires_at timestamptz NOT NULL,
 revoked_at timestamptz
);
CREATE INDEX oauth_live_sessions ON oauth_login_sessions(actor,expires_at) WHERE revoked_at IS NULL;
CREATE TABLE oauth_identity_events (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 actor text NOT NULL REFERENCES oauth_accounts(actor),
 event text NOT NULL CHECK(event IN ('signup','login','link','session-created','session-revoked')),
 provider text CHECK(provider IN ('google','github')),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
ALTER TABLE oauth_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE oauth_bindings ENABLE ROW LEVEL SECURITY;
ALTER TABLE oauth_login_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE oauth_identity_events ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON oauth_accounts,oauth_bindings,oauth_login_sessions,oauth_identity_events FROM PUBLIC;

CREATE FUNCTION nsai_oauth_bind(p_provider text,p_subject text,p_mode text,p_target text) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE bound text; account public.oauth_accounts%ROWTYPE;
BEGIN
 IF public.nsai_actor()<>'legacy-service' OR public.nsai_actor_role()<>'service'
    OR nullif(current_setting('nsai.job_id',true),'') IS NOT NULL THEN
  RAISE EXCEPTION 'Authentication service only' USING ERRCODE='42501'; END IF;
 IF p_provider IS NULL OR p_provider NOT IN ('google','github') OR p_subject IS NULL
    OR p_subject !~ '^[a-zA-Z0-9_-]{1,255}$'
    OR (p_provider='github' AND p_subject !~ '^[1-9][0-9]{0,18}$')
    OR p_mode IS NULL OR p_mode NOT IN ('login','signup','link-registry','link-provider') THEN
  RAISE EXCEPTION 'Invalid verified identity binding'; END IF;
 IF (p_mode='login' AND p_target IS NOT NULL)
    OR (p_mode='signup' AND (p_target IS NULL OR p_target !~ '^local-user-oauth-[a-f0-9]{32}$'))
    OR (p_mode IN ('link-registry','link-provider') AND (p_target IS NULL OR p_target !~ '^local-user-[a-z][a-z0-9_-]{0,63}$')) THEN
  RAISE EXCEPTION 'Invalid canonical identity target'; END IF;
 PERFORM pg_advisory_xact_lock(878735);
 SELECT actor INTO bound FROM public.oauth_bindings WHERE provider=p_provider AND subject=p_subject;
 IF bound IS NOT NULL THEN
  IF p_mode LIKE 'link-%' AND bound<>p_target THEN
   RAISE EXCEPTION 'Provider identity is already linked' USING ERRCODE='23505'; END IF;
  IF p_mode='signup' THEN RAISE EXCEPTION 'Provider identity already registered' USING ERRCODE='23505'; END IF;
  SELECT * INTO account FROM public.oauth_accounts WHERE actor=bound;
  IF p_mode LIKE 'link-%' AND account.authority<>(CASE WHEN p_mode='link-registry' THEN 'registry' ELSE 'provider' END) THEN
   RAISE EXCEPTION 'Canonical account authority conflict' USING ERRCODE='28000'; END IF;
 ELSE
  IF p_mode='login' THEN RAISE EXCEPTION 'Provider identity is not registered' USING ERRCODE='28000'; END IF;
  IF NOT EXISTS(SELECT 1 FROM public.oauth_accounts WHERE actor=p_target)
     AND (SELECT count(*) FROM public.oauth_accounts)>=10000 THEN RAISE EXCEPTION 'Account capacity exceeded'; END IF;
  IF p_mode='signup' THEN
   INSERT INTO public.oauth_accounts(actor,authority) VALUES(p_target,'provider');
  ELSIF p_mode='link-registry' THEN
   INSERT INTO public.oauth_accounts(actor,authority) VALUES(p_target,'registry') ON CONFLICT DO NOTHING;
  END IF;
  SELECT * INTO account FROM public.oauth_accounts WHERE actor=p_target;
  IF NOT FOUND OR NOT account.enabled OR account.authority<>(CASE WHEN p_mode='link-registry' THEN 'registry' ELSE 'provider' END) THEN
   RAISE EXCEPTION 'Canonical account unavailable' USING ERRCODE='28000'; END IF;
  INSERT INTO public.oauth_bindings(provider,subject,actor) VALUES(p_provider,p_subject,account.actor);
 END IF;
 IF NOT account.enabled THEN RAISE EXCEPTION 'Canonical account unavailable' USING ERRCODE='28000'; END IF;
 INSERT INTO public.oauth_identity_events(actor,event,provider)
  VALUES(account.actor,CASE WHEN p_mode LIKE 'link-%' THEN 'link' ELSE p_mode END,p_provider);
 RETURN jsonb_build_object('actor',account.actor,'authority',account.authority);
END $$;

CREATE FUNCTION nsai_oauth_session_create(p_token text,p_csrf text,p_actor text,p_hours integer) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
BEGIN
 IF public.nsai_actor()<>'legacy-service' OR public.nsai_actor_role()<>'service'
    OR nullif(current_setting('nsai.job_id',true),'') IS NOT NULL THEN
  RAISE EXCEPTION 'Authentication service only' USING ERRCODE='42501'; END IF;
 IF p_token IS NULL OR p_token !~ '^[a-f0-9]{64}$' OR p_csrf IS NULL OR p_csrf !~ '^[a-f0-9]{64}$'
    OR p_actor IS NULL OR p_hours IS NULL OR p_hours NOT BETWEEN 1 AND 24 THEN
  RAISE EXCEPTION 'Invalid login session'; END IF;
 PERFORM pg_advisory_xact_lock(878735);
 IF NOT EXISTS(SELECT 1 FROM public.oauth_accounts WHERE actor=p_actor AND enabled) THEN
  RAISE EXCEPTION 'Canonical account unavailable' USING ERRCODE='28000'; END IF;
 IF (SELECT count(*) FROM public.oauth_login_sessions WHERE actor=p_actor AND revoked_at IS NULL AND expires_at>clock_timestamp())>=16
    OR (SELECT count(*) FROM public.oauth_login_sessions)>=100000 THEN
  RAISE EXCEPTION 'Login session capacity exceeded'; END IF;
 INSERT INTO public.oauth_login_sessions(token_hash,csrf_hash,actor,expires_at)
  VALUES(p_token,p_csrf,p_actor,clock_timestamp()+make_interval(hours=>p_hours));
 INSERT INTO public.oauth_identity_events(actor,event) VALUES(p_actor,'session-created');
END $$;

CREATE FUNCTION nsai_oauth_session_resolve(p_token text) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE result jsonb;
BEGIN
 IF nullif(current_setting('nsai.job_id',true),'') IS NOT NULL THEN
  RAISE EXCEPTION 'Login session unavailable' USING ERRCODE='42501'; END IF;
 SELECT jsonb_build_object('actor',a.actor,'authority',a.authority,'csrf_hash',s.csrf_hash) INTO result
 FROM public.oauth_login_sessions s JOIN public.oauth_accounts a ON a.actor=s.actor
 WHERE s.token_hash=p_token AND s.revoked_at IS NULL AND s.expires_at>clock_timestamp() AND a.enabled
 AND ((public.nsai_actor()='legacy-service' AND public.nsai_actor_role()='service')
      OR (public.nsai_actor()=a.actor AND public.nsai_actor_role() IN ('operator','viewer','reviewer','admin')));
 RETURN result;
END $$;

CREATE FUNCTION nsai_oauth_session_revoke(p_token text) RETURNS boolean
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE target text;
BEGIN
 IF nullif(current_setting('nsai.job_id',true),'') IS NOT NULL THEN
  RAISE EXCEPTION 'Login session unavailable' USING ERRCODE='42501'; END IF;
 UPDATE public.oauth_login_sessions SET revoked_at=clock_timestamp()
 WHERE token_hash=p_token AND revoked_at IS NULL
 AND ((public.nsai_actor()='legacy-service' AND public.nsai_actor_role()='service')
      OR actor=public.nsai_actor()) RETURNING actor INTO target;
 IF target IS NULL THEN RETURN false; END IF;
 INSERT INTO public.oauth_identity_events(actor,event) VALUES(target,'session-revoked');
 RETURN true;
END $$;
REVOKE ALL ON FUNCTION nsai_oauth_bind(text,text,text,text),
 nsai_oauth_session_create(text,text,text,integer),nsai_oauth_session_resolve(text),nsai_oauth_session_revoke(text) FROM PUBLIC;
