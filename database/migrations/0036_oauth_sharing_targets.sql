-- An owner can validate a supplied opaque provider actor without a global
-- account directory, provider profiles, session tokens or direct table access.
CREATE FUNCTION nsai_current_oauth_sharing_target(doc text,target text) RETURNS boolean
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
BEGIN
 PERFORM public.nsai_current_source_access(doc);
 IF target IS NULL OR target !~ '^local-user-oauth-[a-f0-9]{32}$' THEN RETURN false; END IF;
 RETURN EXISTS(SELECT 1 FROM public.oauth_accounts
               WHERE actor=target AND authority='provider' AND enabled);
END $$;
REVOKE ALL ON FUNCTION nsai_current_oauth_sharing_target(text,text) FROM PUBLIC;
