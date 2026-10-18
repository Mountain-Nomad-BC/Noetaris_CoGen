from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from nsai.contracts import CandidateClaim, EvidenceSource, IndexGeneration, SkillProposal, canonical_hash
from nsai.learning.gates import assess_candidate
from nsai.retrieval.fusion import reciprocal_rank_fusion


def source():
    return EvidenceSource(document_id="doc_12345678",revision="rev2",content_sha256="a"*64,locator="page:3",media_type="application/pdf")

def test_candidate_never_verified_by_default():
    c=CandidateClaim(claim_id="claim_1234",subject="pump",predicate="limit",value="75C",source=source(),observed_at=datetime.now(timezone.utc))
    assert c.state.value=="candidate"
    assert len(canonical_hash(c))==64

def test_extra_authority_flags_rejected():
    with pytest.raises(ValidationError):
        CandidateClaim(claim_id="claim_1234",subject="pump",predicate="limit",value="75C",source=source(),observed_at=datetime.now(timezone.utc),authority_granted=True)

def test_index_activation_without_test_fails():
    with pytest.raises(ValidationError):
        IndexGeneration(generation_id="generation_123",source_set_sha256="0"*64,embedder_identity="model@digest",index_sha256="a"*64,activated=True)

def test_skills_cannot_self_authorize_execution():
    with pytest.raises(ValidationError):
        SkillProposal(proposal_id="proposal_123",description="test",inputs_schema_sha256="0"*64,execution_enabled=True)

def test_gate_reports_independent_blockers():
    decision=assess_candidate(source_count=1,conflicting=True,eval_total=10,eval_passed=9,authorized_reviewer_present=False)
    assert not decision.eligible_for_review and len(decision.reasons)==3

def test_deterministic_fusion_and_dedupe():
    x=reciprocal_rank_fusion([["x","y","x"],["y","x"]])
    assert x == reciprocal_rank_fusion([["x","y","x"],["y","x"]])
    assert len(x)==2
