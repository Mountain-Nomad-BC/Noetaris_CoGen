-- Broad and entity/source-scoped searches need different plans. PostgreSQL's
-- generic plan became slower after the fifth call on a reused connection.
-- This function-local setting also applies to its nested authorization queries;
-- it restores the caller's setting on return and does not change SQL deadlines.
ALTER FUNCTION nsai_library_lexical_search(text,text,text,text[],text,integer[],integer)
  SET plan_cache_mode=force_custom_plan;
