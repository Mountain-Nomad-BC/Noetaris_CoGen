import pytest
from nsai.source_dependencies import collect_sources,stamp_result,stored_provenance


def test_multi_source_memory_and_uncited_prompt_inputs_remain_dependencies():
    result=dict(citations=[dict(document_id='cited')],answer='Supported answer')
    stamp_result(result,[dict(document_id='uncited-prompt-input')],
                 dict(working=[dict(source_ids=['private-memory-source'])]))
    assert result['source_dependencies']==['cited','private-memory-source','uncited-prompt-input']
    assert result['provenance_complete'] is True


def test_graph_edges_and_conflicts_include_every_contributing_source():
    assert collect_sources(dict(edges=[dict(provenance=dict(document_id='manual'))],
                                alternatives={'85C':[dict(document_id='paper')]}),
                           required=['primary'])==['manual','paper','primary']


def test_old_receipt_citations_cannot_claim_complete_provenance():
    assert stored_provenance(dict(citations=[dict(document_id='known')]))==([],False)
    assert stored_provenance(dict(provenance_complete=True,source_dependencies=[]))==([],True)


@pytest.mark.parametrize('value',[dict(document_id=[]),dict(document_id=''),
                                 dict(source_ids='manual'),dict(source_ids=[None]),
                                 dict(source_dependencies=[1])])
def test_invalid_dependency_shapes_fail_closed(value):
    with pytest.raises(ValueError):collect_sources(value)


def test_dependency_size_and_depth_are_bounded():
    with pytest.raises(ValueError):collect_sources(dict(source_ids=[str(n) for n in range(1001)]))
    value={}
    for _ in range(34):value=dict(child=value)
    with pytest.raises(ValueError):collect_sources(value)


def test_large_size_checked_research_walk_preserves_late_foreign_dependencies():
    from nsai.source_dependencies import RESEARCH_VISIT_BUDGET
    artifact={'nodes':[dict(text='x',fields=list(range(12))) for _ in range(10000)],
              'last_edge':{'provenance':{'document_id':'foreign'}}}
    with pytest.raises(ValueError,match='traversal budget'):collect_sources(artifact,required=['primary'])
    assert collect_sources(artifact,required=['primary'],traversal_budget=RESEARCH_VISIT_BUDGET)==['foreign','primary']


def test_research_walk_never_relaxes_source_count_depth_or_its_own_visit_bound():
    from nsai.source_dependencies import RESEARCH_VISIT_BUDGET
    with pytest.raises(ValueError,match='dependency budget'):
        collect_sources(dict(source_ids=[str(n) for n in range(1001)]),traversal_budget=RESEARCH_VISIT_BUDGET)
    deep={}
    for _ in range(34):deep={'child':deep}
    with pytest.raises(ValueError,match='traversal budget'):collect_sources(deep,traversal_budget=RESEARCH_VISIT_BUDGET)
    with pytest.raises(ValueError,match='traversal budget'):collect_sources([0]*RESEARCH_VISIT_BUDGET,traversal_budget=RESEARCH_VISIT_BUDGET)
    with pytest.raises(ValueError,match='Invalid source dependency traversal budget'):collect_sources({},traversal_budget=RESEARCH_VISIT_BUDGET+1)


def test_manifest_resolution_keeps_complete_sources_and_reuses_active_transaction(monkeypatch):
    from nsai import provenance_manifests
    connection=object();calls=[]
    def resolve(identity,*,conn=None):
        calls.append(identity);assert conn is connection
        return ['private','shared']
    monkeypatch.setattr(provenance_manifests,'get_sources',resolve)
    value=dict(source_manifest_id='a'*32,children=[dict(source_manifest_id='a'*32)])
    assert collect_sources(value,required=['direct'],conn=connection)==['direct','private','shared']
    assert calls==['a'*32]


def test_manifest_resolution_failure_never_silently_drops_dependencies(monkeypatch):
    from nsai import provenance_manifests
    def unavailable(*a,**kw):raise LookupError('Source unavailable')
    monkeypatch.setattr(provenance_manifests,'get_sources',unavailable)
    with pytest.raises(LookupError):stored_provenance(dict(provenance_complete=True,source_manifest_id='a'*32))
