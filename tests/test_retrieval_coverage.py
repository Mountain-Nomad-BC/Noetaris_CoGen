import json
from nsai.workflow_store import RetrievalHits

def test_zero_matches_are_exact_lexical_zero():
    hits=RetrievalHits([],12)
    assert hits==[] and hits.coverage==dict(method='lexical',returned_chunks=0,limit=12,additional_matches_exist=False,matching_chunks_lower_bound=0,omitted_chunks_at_least=0,total_matching_chunks=0)

def test_exact_limit_does_not_invent_omission():
    hits=RetrievalHits(list(range(12)),12)
    assert hits.coverage['total_matching_chunks']==12 and not hits.coverage['additional_matches_exist']
    assert hits.coverage['omitted_chunks_at_least']==0

def test_sentinel_is_not_returned_and_does_not_claim_exact_total():
    hits=RetrievalHits(list(range(13)),12)
    assert hits==list(range(12)) and hits.coverage['additional_matches_exist']
    assert hits.coverage['matching_chunks_lower_bound']==13 and hits.coverage['total_matching_chunks'] is None and hits.coverage['omitted_chunks_at_least']==1

def test_existing_list_iteration_index_slice_and_json_contract():
    hits=RetrievalHits([{'id':'a'},{'id':'b'}],1)
    assert isinstance(hits,list) and hits[0]=={'id':'a'} and list(hits)==[{'id':'a'}]
    assert type(hits[:]) is list and json.loads(json.dumps(hits))==[{'id':'a'}]
