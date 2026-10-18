-- Owner-only management projection. Shared readers and admin roles alone have
-- no visibility into another source's grants or management metadata.
CREATE FUNCTION nsai_current_source_access(doc text) RETURNS jsonb
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE result jsonb;
BEGIN
  IF coalesce(current_setting('nsai.job_id',true),'')<>'' OR
    public.nsai_actor() !~ '^local-user-[a-z][a-z0-9_-]{0,63}$' OR
    NOT EXISTS(SELECT 1 FROM public.document_owners WHERE document_id=doc AND owner_actor=public.nsai_actor())
    THEN RAISE EXCEPTION 'Source unavailable' USING ERRCODE='42501'; END IF;
  SELECT jsonb_build_object('document_id',doc,'owner',o.owner_actor,'epoch',v.epoch,
    'grants',coalesce((SELECT jsonb_agg(jsonb_build_object('subject_kind',g.subject_kind,
      'subject_id',g.subject_id,'expires_at',g.expires_at,'revoked',g.revoked)
      ORDER BY g.subject_kind,g.subject_id) FROM public.document_read_grants g WHERE g.document_id=doc),'[]'::jsonb))
    INTO result FROM public.document_owners o JOIN public.document_policy_versions v USING(document_id)
    WHERE o.document_id=doc;
  RETURN result;
END $$;

CREATE FUNCTION nsai_current_source_share(doc text,expected_epoch bigint,kind text,
  subject text,expiry timestamptz,revoke boolean) RETURNS bigint
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
BEGIN
  PERFORM public.nsai_current_source_access(doc);
  RETURN public.nsai_private_share(doc,public.nsai_actor(),expected_epoch,kind,subject,expiry,revoke);
END $$;
REVOKE ALL ON FUNCTION nsai_current_source_access(text),
  nsai_current_source_share(text,bigint,text,text,timestamptz,boolean) FROM PUBLIC;
