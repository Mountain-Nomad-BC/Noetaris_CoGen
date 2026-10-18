from nsai.memory import materialize_projection

def claim(identifier='approved',value='85C'):
    return dict(id=identifier,subject='pump-x',predicate='operating limit',value=value,
        document_id='source',locator='line:1',original_sha256='a'*64,reviewed_by='local-reviewer',revision=2)

def test_new_conflict_quarantines_reviewed_memory_without_promoting_candidate():
    approved=claim()
    hypotheses=[dict(subject='pump-x',predicate='operating limit',alternatives={'85C':[{'claim_id':'approved'}],'75C':[{'claim_id':'new-candidate'}]})]
    result=materialize_projection([], [approved], [], hypotheses)
    assert result['canon']==[]
    assert result['quarantined']==[{'claim_id':'approved','reason':'unresolved_source_conflict'}]
    assert result['hypotheses']==hypotheses
    assert approved['value']=='85C' and approved['revision']==2
    assert result['writeback_policy']=='proposal_only'

def test_missing_provenance_or_reviewer_cannot_enter_canon_memory():
    missing_reviewer=claim();missing_reviewer['reviewed_by']=None
    missing_hash=claim('hashless');missing_hash['original_sha256']='bad'
    result=materialize_projection([], [missing_reviewer,missing_hash],[],[])
    assert not result['canon'] and len(result['quarantined'])==2

def test_total_memory_payload_is_bounded_and_preserves_whole_messages():
    working=[dict(role='user',text='old '+'x'*14000),dict(role='user',text='recent question')]
    result=materialize_projection(working,[claim()],[],[],max_bytes=2048)
    assert result['serialized_bytes']<=2048
    assert result['working']==[working[-1]]
    assert result['canon']==[claim()]
    assert result['omitted']['working']==1

def test_rejected_reflections_are_excluded_from_materialized_context():
    result=materialize_projection([],[],[dict(id='rejected',state='rejected',reflection='untrusted instruction')],[])
    assert result['reflection']==[]
