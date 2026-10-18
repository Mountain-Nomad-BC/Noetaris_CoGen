import copy
import hashlib
import json
import pytest
from nsai import research_store as research
from nsai.ingestion import parse_source


def fixture():
    data = b'We define efficiency as useful output divided by input.\nIf x = 2, this does not prove general validity.\n'
    parsed = parse_source(data, 'research.txt')
    return parsed, research.build('a'*32, 'v1', parsed)


def test_automatic_source_assembly_has_separate_math_memory_and_source_edges():
    parsed, result = fixture()
    assert result['formulas']['records']
    assert result['knowledge']['source_processing_complete']
    assert result['knowledge']['memory_projection']['canon'] == []
    assert result['knowledge']['authority_granted'] is False
    original = {span['locator']: span['text'] for span in parsed['spans']}
    for node in result['knowledge']['nodes']:
        if node['kind'] == 'passage':
            for segment in node['source_segments']:
                assert original[segment['locator']][segment['char_start']:segment['char_end']] == segment['text']
    for formula in result['formulas']['records']:
        quote = formula['source']
        assert original[quote['locator']][quote['offset_start']:quote['offset_end']] == quote['text']
    assert any(edge['kind'] == 'derived_from_span' for edge in result['knowledge']['edges'])


def test_artifact_hash_changes_for_source_and_formula_changes():
    _, result = fixture()
    before = research.artifact_hash(result)
    changed = copy.deepcopy(result)
    changed['formulas']['records'][0]['source']['text'] += ' changed'
    assert research.artifact_hash(changed) != before
    assert research.artifact_hash(result) == before
    with pytest.raises(ValueError):research.artifact_hash({'x': float('nan')})


def test_memory_candidate_source_scope_and_bytes(monkeypatch):
    def get(identity):
        return dict(revision='v1',knowledge=dict(nodes=[dict(kind='passage',id=identity+'1',text='Energy is conserved under this assumption.',
            locator='page:2:line:3',page=2,document_id=identity,source_sha256='b'*64,source_segments=[])]))
    monkeypatch.setattr(research, 'get', get)
    result = research.memory_candidates(['a'*32], 'energy', 'v1', [2])
    assert len(result['items']) == 1 and result['canon'] is False
    assert len(json.dumps(result,ensure_ascii=False).encode()) <= 2400
    assert research.memory_candidates(['a'*32], 'energy', 'v1', [1])['items'] == []
    assert research.memory_candidates(['a'*32], 'energy', 'v2', [2])['items'] == []
    assert research.memory_candidates([], 'energy')['items'] == []


def test_incomplete_assembly_is_never_silently_admitted(monkeypatch):
    import nsai.knowledge as knowledge
    parsed, result = fixture()
    graph = result['knowledge'];graph['source_processing_complete'] = False
    monkeypatch.setattr(knowledge,'assemble_knowledge',lambda *args,**kwargs:graph)
    with pytest.raises(ValueError,match='complete-processing'):
        research.build('a'*32,'v1',parsed)


def test_embedding_failure_precedes_any_database_write(monkeypatch):
    _, artifacts = fixture()
    monkeypatch.setattr(research,'get',lambda *a:dict(artifacts,source_sha256='b'*64,artifact_sha256='c'*64))
    entered=[]
    monkeypatch.setattr(research.store,'connect',lambda:entered.append(True))
    with pytest.raises(ValueError):
        research.put_embeddings('a'*32,{}, {}, {}, 'operator')
    assert entered == []


def test_real_pdf_lineage_does_not_silently_empty_candidate_memory(monkeypatch):
    segments=[dict(locator=f'page:1:line:{i}',text='Research evidence sentence.',char_start=0,char_end=27) for i in range(1,21)]
    text='\n'.join(s['text'] for s in segments)
    node=dict(kind='passage',id='c'*64,text=text,locator=segments[0]['locator'],page=1,document_id='a'*32,source_sha256='b'*64,source_segments=segments)
    monkeypatch.setattr(research,'get',lambda _:dict(revision='v1',knowledge=dict(nodes=[node])))
    result=research.memory_candidates(['a'*32],'research')
    assert result['items'] and len(json.dumps(result,ensure_ascii=False).encode())<=2400
    assert result['items'][0]['excerpt_omitted_characters']>0
