-- Bind insert checks to the proposal, not the candidate claim's derived fields.
-- Candidate source claims may legitimately have no reviewed derived provenance.
-- This changes no stored rows, ownership, grants or independent-review policy.
DROP POLICY learning_create ON learning_proposals;
CREATE POLICY learning_create ON learning_proposals FOR INSERT WITH CHECK
 (EXISTS(SELECT 1 FROM claims c WHERE c.id=learning_proposals.source_claim_id AND
   ((nsai_legacy_context() AND learning_proposals.author NOT LIKE 'local-user-%') OR
    (learning_proposals.author=nsai_actor()
     AND c.document_id=ANY(learning_proposals.source_ids)
     AND nsai_sources_visible(learning_proposals.source_ids,learning_proposals.provenance_complete)))));
