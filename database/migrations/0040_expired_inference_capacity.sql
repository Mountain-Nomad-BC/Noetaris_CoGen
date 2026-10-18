-- Expired reservations no longer hold a global inference slot while their
-- owner is inactive and therefore unable to trigger owner-scoped reconciliation.
CREATE OR REPLACE FUNCTION nsai_active_inference_count() RETURNS bigint
LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,public AS $$
  SELECT count(*) FROM public.inference_runs
  WHERE state='reserved' AND created_at>=now()-interval '300 seconds';
$$;
REVOKE ALL ON FUNCTION nsai_active_inference_count() FROM PUBLIC;
