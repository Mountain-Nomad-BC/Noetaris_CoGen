-- Account only rows actually inserted: BEFORE INSERT also fires for ignored
-- ON CONFLICT attempts, which must not consume canonical artifact capacity.
DROP TRIGGER semantic_storage_account ON knowledge_embeddings;
UPDATE semantic_storage_usage SET canonical_bytes=
  (SELECT coalesce(sum(octet_length(payload::text)),0) FROM knowledge_embeddings);
CREATE TRIGGER semantic_storage_account AFTER INSERT OR UPDATE OR DELETE ON knowledge_embeddings
  FOR EACH ROW EXECUTE FUNCTION nsai_semantic_storage_account();

-- Resource limits span every owner without exposing another owner's records.
CREATE TABLE governed_storage_usage (
  singleton boolean PRIMARY KEY DEFAULT true CHECK(singleton),
  record_count bigint NOT NULL CHECK(record_count>=0 AND record_count<=2000),
  canonical_bytes bigint NOT NULL CHECK(canonical_bytes>=0 AND canonical_bytes<=134217728)
);
INSERT INTO governed_storage_usage(singleton,record_count,canonical_bytes)
  SELECT true,count(*),coalesce(sum(octet_length(payload::text)),0) FROM governed_records;

CREATE FUNCTION nsai_governed_storage_account() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE previous_bytes bigint=0; next_bytes bigint=0; delta integer=0;
  used bigint; records bigint;
BEGIN
  IF TG_OP='UPDATE' AND NEW.payload IS NOT DISTINCT FROM OLD.payload THEN RETURN NEW; END IF;
  IF TG_OP<>'INSERT' THEN previous_bytes=octet_length(OLD.payload::text); END IF;
  IF TG_OP<>'DELETE' THEN next_bytes=octet_length(NEW.payload::text); END IF;
  IF TG_OP='INSERT' THEN delta=1; ELSIF TG_OP='DELETE' THEN delta=-1; END IF;
  -- AFTER triggers run only after the row's existing RLS/source checks. The
  -- counter and row roll back together on capacity failure or caller rollback.
  PERFORM pg_advisory_xact_lock(878711);
  SELECT record_count,canonical_bytes INTO STRICT records,used
    FROM public.governed_storage_usage WHERE singleton FOR UPDATE;
  IF records+delta>2000 OR used-previous_bytes+next_bytes>134217728 OR next_bytes>16777216 THEN
    RAISE EXCEPTION 'Governed artifact capacity reached' USING ERRCODE='54000';
  END IF;
  UPDATE public.governed_storage_usage SET record_count=records+delta,
    canonical_bytes=used-previous_bytes+next_bytes WHERE singleton;
  IF TG_OP='DELETE' THEN RETURN OLD; END IF;
  RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION nsai_governed_storage_account() FROM PUBLIC;
CREATE TRIGGER governed_storage_account AFTER INSERT OR UPDATE OR DELETE ON governed_records
  FOR EACH ROW EXECUTE FUNCTION nsai_governed_storage_account();
