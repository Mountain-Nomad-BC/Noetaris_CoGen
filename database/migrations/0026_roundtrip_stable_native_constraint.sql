-- BETWEEN inside a larger conjunction deparses to nested Boolean AND nodes.
-- pg_dump/restore reparses those into a flat conjunction, changing the sealed
-- constraint definition despite identical semantics. Declare the equivalent
-- flat comparisons directly so a genuine restore preserves the exact seal.
ALTER TABLE native_semantic_passages DROP CONSTRAINT native_semantic_passages_check;
ALTER TABLE native_semantic_passages ADD CONSTRAINT native_semantic_passages_check
  CHECK(cardinality(source_ids)>=1 AND cardinality(source_ids)<=1000
    AND array_position(source_ids,NULL) IS NULL AND document_id=ANY(source_ids));
