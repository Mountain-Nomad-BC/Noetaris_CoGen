-- Persistence foundation only. Existing content admission remains closed to
-- individual principals until all content and derived paths are integrated.
-- Legacy sources deliberately have no ownership row: never guess an owner.
CREATE TABLE document_owners (
  document_id text PRIMARY KEY REFERENCES documents(id),
  owner_actor text NOT NULL CHECK(owner_actor ~ '^local-user-[a-z][a-z0-9_-]{0,63}$'),
  created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE TRIGGER document_owners_immutable BEFORE UPDATE OR DELETE ON document_owners
  FOR EACH ROW EXECUTE FUNCTION nsai_refuse_update_delete();
CREATE TABLE document_policy_versions (
  document_id text PRIMARY KEY REFERENCES document_owners(document_id),
  epoch bigint NOT NULL DEFAULT 1 CHECK(epoch > 0)
);
CREATE TABLE document_read_grants (
  document_id text NOT NULL REFERENCES document_owners(document_id),
  subject_kind text NOT NULL CHECK(subject_kind IN ('user','group')),
  subject_id text NOT NULL CHECK(length(subject_id) BETWEEN 1 AND 128),
  expires_at timestamptz,
  revoked boolean NOT NULL DEFAULT false,
  PRIMARY KEY(document_id,subject_kind,subject_id),
  CHECK(subject_kind <> 'user' OR subject_id ~ '^local-user-[a-z][a-z0-9_-]{0,63}$')
);
CREATE TABLE private_groups (
  group_id text PRIMARY KEY CHECK(group_id ~ '^[a-z][a-z0-9_-]{0,63}$'),
  epoch bigint NOT NULL DEFAULT 1 CHECK(epoch > 0)
);
CREATE TABLE private_group_members (
  group_id text NOT NULL REFERENCES private_groups(group_id),
  actor text NOT NULL CHECK(actor ~ '^local-user-[a-z][a-z0-9_-]{0,63}$'),
  PRIMARY KEY(group_id,actor)
);
CREATE TABLE private_access_events (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  document_id text REFERENCES document_owners(document_id),
  group_id text REFERENCES private_groups(group_id),
  actor text NOT NULL,
  event_type text NOT NULL CHECK(event_type IN ('owner','share','revoke','membership-add','membership-remove','privileged-read')),
  epoch bigint NOT NULL CHECK(epoch > 0),
  details jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  CHECK((document_id IS NULL) <> (group_id IS NULL))
);
CREATE TRIGGER private_access_events_immutable BEFORE UPDATE OR DELETE ON private_access_events
  FOR EACH ROW EXECUTE FUNCTION nsai_refuse_update_delete();

-- Functions accept server-resolved actors, never request-supplied identities.
-- These are trusted-server seams, not an SQL-injection security boundary.
CREATE FUNCTION nsai_private_own(doc text, actor text) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, public AS $$
BEGIN
  -- Only new sources in this transaction may acquire an uploader identity.
  -- Mapping quarantined legacy evidence requires a separate explicit process.
  IF NOT EXISTS(SELECT 1 FROM public.documents WHERE id=doc AND xmin=pg_current_xact_id()::xid)
    THEN RAISE EXCEPTION 'Ownership requires a new source transaction'; END IF;
  INSERT INTO public.document_owners(document_id,owner_actor) VALUES(doc,actor);
  INSERT INTO public.document_policy_versions(document_id) VALUES(doc);
  INSERT INTO public.private_access_events(document_id,actor,event_type,epoch)
    VALUES(doc,actor,'owner',1);
END $$;

CREATE FUNCTION nsai_private_share(doc text, actor text, expected_epoch bigint,
  kind text, subject text, expiry timestamptz, revoke boolean) RETURNS bigint
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, public AS $$
DECLARE next_epoch bigint;
BEGIN
  IF NOT EXISTS(SELECT 1 FROM public.document_owners WHERE document_id=doc AND owner_actor=actor)
    THEN RAISE EXCEPTION 'Source unavailable' USING ERRCODE='42501'; END IF;
  IF revoke IS NULL OR (expiry IS NOT NULL AND expiry <= clock_timestamp())
    THEN RAISE EXCEPTION 'Invalid grant'; END IF;
  IF kind='group' AND NOT EXISTS(SELECT 1 FROM public.private_groups WHERE group_id=subject)
    THEN RAISE EXCEPTION 'Invalid group'; END IF;
  UPDATE public.document_policy_versions SET epoch=epoch+1
    WHERE document_id=doc AND epoch=expected_epoch RETURNING epoch INTO next_epoch;
  IF next_epoch IS NULL THEN RAISE EXCEPTION 'Stale policy' USING ERRCODE='40001'; END IF;
  INSERT INTO public.document_read_grants VALUES(doc,kind,subject,expiry,revoke)
    ON CONFLICT(document_id,subject_kind,subject_id) DO UPDATE
    SET expires_at=EXCLUDED.expires_at,revoked=EXCLUDED.revoked;
  INSERT INTO public.private_access_events(document_id,actor,event_type,epoch,details)
    VALUES(doc,actor,CASE WHEN revoke THEN 'revoke' ELSE 'share' END,next_epoch,
      jsonb_build_object('subject_kind',kind,'subject_id',subject,'expires_at',expiry));
  RETURN next_epoch;
END $$;

-- Group provisioning and membership changes are deployment-owner operations;
-- the application role cannot call this function or mutate membership tables.
CREATE FUNCTION nsai_private_membership(grp text, member_actor text, admin_actor text,
  expected_epoch bigint, remove_member boolean) RETURNS bigint
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, public AS $$
DECLARE next_epoch bigint;
BEGIN
  IF remove_member IS NULL THEN RAISE EXCEPTION 'Invalid membership'; END IF;
  UPDATE public.private_groups SET epoch=epoch+1 WHERE group_id=grp AND epoch=expected_epoch
    RETURNING epoch INTO next_epoch;
  IF next_epoch IS NULL THEN RAISE EXCEPTION 'Stale membership' USING ERRCODE='40001'; END IF;
  IF remove_member THEN
    DELETE FROM public.private_group_members WHERE group_id=grp AND actor=member_actor;
  ELSE
    INSERT INTO public.private_group_members VALUES(grp,member_actor) ON CONFLICT DO NOTHING;
  END IF;
  INSERT INTO public.private_access_events(group_id,actor,event_type,epoch,details)
    VALUES(grp,admin_actor,CASE WHEN remove_member THEN 'membership-remove' ELSE 'membership-add' END,
      next_epoch,jsonb_build_object('member',member_actor));
  RETURN next_epoch;
END $$;

CREATE FUNCTION nsai_private_can_read(doc text, actor text) RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog, public AS $$
  SELECT EXISTS(SELECT 1 FROM public.document_owners o WHERE o.document_id=doc AND
    (o.owner_actor=actor OR EXISTS(SELECT 1 FROM public.document_read_grants g
      WHERE g.document_id=doc AND NOT g.revoked
        AND (g.expires_at IS NULL OR g.expires_at > statement_timestamp())
        AND ((g.subject_kind='user' AND g.subject_id=actor) OR
          (g.subject_kind='group' AND EXISTS(SELECT 1 FROM public.private_group_members m
            WHERE m.group_id=g.subject_id AND m.actor=actor))))));
$$;

-- Future content adapters must commit this transaction before releasing bytes,
-- and reauthorize each contributing source immediately before serialization.
-- This function alone does not enforce access on content/derived tables.
CREATE FUNCTION nsai_private_authorize_read(doc text, actor text, actor_role text) RETURNS bigint
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, public AS $$
DECLARE current_epoch bigint;
BEGIN
  IF actor_role IS NULL OR actor_role NOT IN ('operator','viewer','reviewer','admin')
    THEN RAISE EXCEPTION 'Invalid role' USING ERRCODE='42501'; END IF;
  SELECT epoch INTO current_epoch FROM public.document_policy_versions
    WHERE document_id=doc FOR SHARE;
  -- Serialize group removal with this authorization/audit transaction, too.
  PERFORM p.group_id FROM public.private_groups p
    JOIN public.document_read_grants g ON g.subject_kind='group' AND g.subject_id=p.group_id
    WHERE g.document_id=doc ORDER BY p.group_id FOR SHARE OF p;
  IF current_epoch IS NULL OR NOT public.nsai_private_can_read(doc,actor)
    THEN RAISE EXCEPTION 'Source unavailable' USING ERRCODE='42501'; END IF;
  IF actor_role='admin' THEN
    INSERT INTO public.private_access_events(document_id,actor,event_type,epoch)
      VALUES(doc,actor,'privileged-read',current_epoch);
  END IF;
  RETURN current_epoch;
END $$;

REVOKE ALL ON FUNCTION nsai_private_own(text,text) FROM PUBLIC;
REVOKE ALL ON FUNCTION nsai_private_share(text,text,bigint,text,text,timestamptz,boolean) FROM PUBLIC;
REVOKE ALL ON FUNCTION nsai_private_membership(text,text,text,bigint,boolean) FROM PUBLIC;
REVOKE ALL ON FUNCTION nsai_private_can_read(text,text) FROM PUBLIC;
REVOKE ALL ON FUNCTION nsai_private_authorize_read(text,text,text) FROM PUBLIC;
