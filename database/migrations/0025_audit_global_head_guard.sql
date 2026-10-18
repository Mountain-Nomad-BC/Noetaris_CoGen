-- Refuse an already forked ledger; never repair history by rewriting events.
DO $$ BEGIN
  IF EXISTS(SELECT 1 FROM (
    SELECT previous_sha256,lag(sha256,1,repeat('0',64)) OVER(ORDER BY id) expected
    FROM public.audit_events
  ) chain WHERE previous_sha256 IS DISTINCT FROM expected) THEN
    RAISE EXCEPTION 'Audit continuity requires owner-side investigation';
  END IF;
END $$;

CREATE FUNCTION nsai_guard_audit_head() RETURNS trigger
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE head_id bigint; head_sha text;
BEGIN
  -- Preserve policy-before-ledger ordering, including direct app INSERTs.
  -- Legacy records with unknown provenance retain their existing RLS behavior.
  IF (session_user='nsai_app' OR current_setting('role',true)='nsai_app')
    AND NEW.provenance_complete AND NOT public.nsai_sources_visible(NEW.source_ids,true) THEN
    RAISE EXCEPTION 'Audit source unavailable' USING ERRCODE='42501';
  END IF;
  PERFORM pg_advisory_xact_lock(878701);
  SELECT id,sha256 INTO head_id,head_sha FROM public.audit_events ORDER BY id DESC LIMIT 1;
  IF NEW.previous_sha256 IS DISTINCT FROM coalesce(head_sha,repeat('0',64))
    OR (head_id IS NOT NULL AND NEW.id<=head_id) THEN
    RAISE EXCEPTION 'Stale audit head; retry with the global head' USING ERRCODE='40001';
  END IF;
  RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION nsai_guard_audit_head() FROM PUBLIC;
CREATE TRIGGER audit_global_head_guard BEFORE INSERT ON audit_events
  FOR EACH ROW EXECUTE FUNCTION nsai_guard_audit_head();
