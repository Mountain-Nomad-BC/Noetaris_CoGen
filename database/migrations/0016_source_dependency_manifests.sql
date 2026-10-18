-- Compact, resolvable provenance keeps bounded prompt-memory envelopes from
-- embedding the entire authorized library's ID set. A reference grants no read.
CREATE TABLE source_dependency_manifests (
  id text PRIMARY KEY DEFAULT replace(gen_random_uuid()::text,'-','') CHECK(id ~ '^[a-f0-9]{32}$'),
  actor text NOT NULL,
  content_sha256 text NOT NULL CHECK(content_sha256 ~ '^[a-f0-9]{64}$'),
  source_ids text[] NOT NULL CHECK(cardinality(source_ids)<=1000 AND array_position(source_ids,NULL) IS NULL),
  created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  UNIQUE(actor,content_sha256)
);
CREATE TRIGGER source_dependency_manifests_immutable BEFORE UPDATE OR DELETE ON source_dependency_manifests
  FOR EACH ROW EXECUTE FUNCTION nsai_refuse_update_delete();

CREATE FUNCTION nsai_register_source_manifest(sources text[]) RETURNS text
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE normalized text[]; checksum text; result text;
BEGIN
  IF coalesce(current_setting('nsai.job_id',true),'')<>'' OR sources IS NULL
    OR cardinality(sources)>1000 OR array_position(sources,NULL) IS NOT NULL
    OR EXISTS(SELECT 1 FROM unnest(sources) value WHERE length(value) NOT BETWEEN 1 AND 128)
    THEN RAISE EXCEPTION 'Invalid request source set' USING ERRCODE='42501'; END IF;
  SELECT coalesce(array_agg(DISTINCT value ORDER BY value),ARRAY[]::text[]) INTO normalized FROM unnest(sources) value;
  IF EXISTS(SELECT 1 FROM unnest(normalized) source WHERE NOT EXISTS(SELECT 1 FROM public.documents WHERE id=source))
    OR NOT public.nsai_sources_visible(normalized,true) THEN
    RAISE EXCEPTION 'Source unavailable' USING ERRCODE='42501'; END IF;
  checksum=encode(sha256(convert_to(array_to_json(normalized)::text,'UTF8')),'hex');
  INSERT INTO public.source_dependency_manifests(actor,content_sha256,source_ids)
    VALUES(public.nsai_actor(),checksum,normalized) ON CONFLICT(actor,content_sha256) DO NOTHING;
  SELECT id INTO result FROM public.source_dependency_manifests
    WHERE actor=public.nsai_actor() AND content_sha256=checksum AND source_ids=normalized;
  IF result IS NULL THEN RAISE EXCEPTION 'Source manifest integrity mismatch'; END IF;
  RETURN result;
END $$;

CREATE FUNCTION nsai_source_manifest_sources(manifest_id text) RETURNS text[]
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE manifest public.source_dependency_manifests;
BEGIN
  IF coalesce(current_setting('nsai.job_id',true),'')<>'' THEN
    RAISE EXCEPTION 'Request context required' USING ERRCODE='42501'; END IF;
  SELECT * INTO manifest FROM public.source_dependency_manifests WHERE id=manifest_id;
  IF NOT FOUND OR EXISTS(SELECT 1 FROM unnest(manifest.source_ids) source WHERE NOT EXISTS(SELECT 1 FROM public.documents WHERE id=source))
    OR NOT public.nsai_sources_visible(manifest.source_ids,true) THEN
    RAISE EXCEPTION 'Source manifest unavailable' USING ERRCODE='42501'; END IF;
  IF manifest.content_sha256<>encode(sha256(convert_to(array_to_json(manifest.source_ids)::text,'UTF8')),'hex') THEN
    RAISE EXCEPTION 'Source manifest integrity mismatch'; END IF;
  RETURN manifest.source_ids;
END $$;
REVOKE ALL ON source_dependency_manifests FROM PUBLIC;
REVOKE ALL ON FUNCTION nsai_register_source_manifest(text[]),nsai_source_manifest_sources(text) FROM PUBLIC;
