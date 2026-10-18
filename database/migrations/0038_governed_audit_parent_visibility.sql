-- Retain historical audit bytes/hashes. Derive read permission from the exact
-- immutable governed referent as well as the audit row's declared sources.
-- Older review audits may list only their origin even though the retained
-- candidate has complete multi-source dependencies. No inference/backfill.
-- Unknown/incomplete governed referents remain withheld until classification.
CREATE POLICY audit_governed_parent_visibility ON audit_events
 AS RESTRICTIVE FOR SELECT USING
 (CASE WHEN lower(event_type) LIKE 'governed.%' THEN
   EXISTS (
     SELECT 1 FROM governed_records g
     WHERE g.id=audit_events.details->>'record_id'
       AND g.document_id=audit_events.details->>'document_id'
       AND g.provenance_complete IS TRUE
       AND g.document_id=ANY(g.source_ids)
       AND (audit_events.event_type='governed.reviewed'
         OR audit_events.event_type='governed.'||g.kind||'.proposed')
       AND nsai_sources_visible(g.source_ids,true)
   )
 ELSE true END);
