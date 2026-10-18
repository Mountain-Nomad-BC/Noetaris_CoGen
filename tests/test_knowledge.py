import json
import math
from pathlib import Path
import pytest
from nsai.knowledge import assemble_knowledge,attach_embeddings,cosine_search,memory_projection
from nsai.semantic_encoder import LocalSemanticEncoder

def graph(**kwargs):
    return assemble_knowledge('a'*32,'v1','b'*64,[dict(locator='page:1',text='Pump condition is not confirmed. If pressure rises, stop the pump.')],**kwargs)

def test_stable_sourcebound_graph_and_explicit_uncertainty():
    first=graph();assert first==graph()
    assert first['source_processing_complete'] and first['authority_granted'] is False
    observations=[n for n in first['nodes'] if n['kind']=='observation']
    assert any(n['negation_cues'] for n in observations) and any(n['condition_cues'] for n in observations)
    assert all(n['source']['source_sha256']=='b'*64 for n in first['nodes'])
    assert not any(e.get('relation_verified') for e in first['edges'])

def test_all_passage_characters_covered_without_silent_truncation():
    text='Testing passage coverage. '*100
    value=assemble_knowledge('a'*32,'v1','b'*64,[dict(locator='page:2',text=text)])
    passages=[n for n in value['nodes'] if n['kind']=='passage']
    assert ''.join(s['text'] for n in passages for s in n['source_segments'])==text
    assert all(len(n['text'])<=600 for n in passages)
    limited=graph(max_nodes=2)
    assert limited['omissions']>0 and limited['source_processing_complete'] is False

def test_formula_attachment_provenance_and_no_evaluation():
    value=graph(formula_nodes=[dict(expression='__import__("os")',source_sha256='b'*64,locator='page:1')])
    assert any(n['kind']=='formula' and n['epistemic_status']=='unverified_formula_proposal' for n in value['nodes'])
    with pytest.raises(ValueError):graph(formula_nodes=[dict(expression='x',source_sha256='c'*64,locator='page:1')])

def embedded():
    value=graph();passages=[n for n in value['nodes'] if n['kind']=='passage'];identity=passages[0]['id']
    return attach_embeddings(value,{identity:[1.]+[0.]*383},dict(name='pinned-real-encoder-contract-fixture',sha256='c'*64,revision='d'*40,dimension=384,pooling='token-mean-overlap-compensated-special-mean'),{identity:dict(input_tokens=10,covered_tokens=10,complete=True,max_sequence_length=256,pooling='token-mean-overlap-compensated-special-mean')})

def test_real_vector_contract_cosine_and_identity_scoped():
    value=embedded();result=cosine_search(value,[1.]+[0.]*383,model_sha256='c'*64)
    assert result[0]['score']==1 and result[0]['relation']=='heuristic_semantic_similarity'
    assert result[0]['authority_granted'] is False
    with pytest.raises(ValueError):cosine_search(value,[1.]+[0.]*383,model_sha256='d'*64)

def test_grouped_passages_preserve_every_segment_without_cross_page():
    spans=[dict(locator='page:1/line:1',text='First original line.'),dict(locator='page:1/line:2',text='Second original line.'),dict(locator='page:2/line:1',text='New page.')]
    value=assemble_knowledge('a'*32,'v1','b'*64,spans)
    passages=[n for n in value['nodes'] if n['kind']=='passage']
    assert len(passages)==2 and passages[0]['text']=='First original line.\nSecond original line.'
    assert [s['locator'] for n in passages for s in n['source_segments']]==[s['locator'] for s in spans]
    for passage in passages:
        for segment in passage['source_segments']:
            original=next(s['text'] for s in spans if s['locator']==segment['locator'])
            assert original[segment['char_start']:segment['char_end']]==segment['text']

def test_partial_and_nonpassage_embeddings_rejected():
    value=embedded();model=value['embeddings']['model_identity'];record=value['embeddings']['records'][0]
    with pytest.raises(ValueError):attach_embeddings(value,{},model,{})
    with pytest.raises(ValueError):attach_embeddings(value,{value['nodes'][0]['id']:record['vector']},model,{value['nodes'][0]['id']:record['coverage']})
    coverage=dict(record['coverage'],complete=False,covered_tokens=1)
    with pytest.raises(ValueError):attach_embeddings(value,{record['node_id']:record['vector']},model,{record['node_id']:coverage})

@pytest.mark.parametrize('vector',[[math.nan,0],[True,0],[0,0],[],[math.inf,1]])
def test_bad_vectors_reject(vector):
    with pytest.raises(ValueError):cosine_search(embedded(),vector,model_sha256='c'*64)

def test_invalid_token_coverage_rejects_false_full_claim():
    value=graph();identity=value['nodes'][0]['id']
    with pytest.raises(ValueError):attach_embeddings(value,{identity:[1,2]},dict(name='fixture',sha256='c'*64),{identity:dict(input_tokens=10,covered_tokens=8,complete=True)})

def test_memory_separate_canon_exact_bounded_bytes():
    value=memory_projection(graph(),max_bytes=1024)
    assert value['canon']==[] and value['state']=='candidate'
    assert len(json.dumps(value,ensure_ascii=False,allow_nan=False).encode())==value['serialized_bytes']<=1024

def test_model_integrity_fails_before_optional_imports(tmp_path):
    manifest=dict(model_id='sentence-transformers/all-MiniLM-L6-v2',revision='a'*40,dimension=384,max_sequence_length=256,files={name:'0'*64 for name in ['model.onnx','tokenizer.json','config.json','tokenizer_config.json','README.md']})
    (tmp_path/'manifest.json').write_text(json.dumps(manifest))
    (tmp_path/'model.onnx').write_bytes(b'modified-model')
    with pytest.raises(ValueError,match='digest mismatch'):LocalSemanticEncoder(tmp_path)

def test_encoder_full_token_window_coverage_and_batch_limit():
    np=pytest.importorskip('numpy')
    encoder=object.__new__(LocalSemanticEncoder);encoder.np=np;encoder.cls=101;encoder.sep=102;encoder.pad=0;encoder.identity=dict(name='synthetic-runtime-fixture')
    class Tokenizer:
        def encode(self,text,add_special_tokens):
            return type('Tokens',(),dict(ids=list(range(1,1001))))()
    class Session:
        def get_inputs(self):return [type('Input',(),dict(name=n))() for n in ('input_ids','attention_mask','token_type_ids')]
        def run(self,outputs,feed):
            assert feed['input_ids'].shape[0]<=8 and feed['input_ids'].shape[1]<=256
            return [np.ones((*feed['input_ids'].shape,384),dtype=np.float32)]
    encoder.tokenizer=Tokenizer();encoder.session=Session()
    value=encoder.encode(['synthetic original long text'])
    assert value['coverage'][0]['input_tokens']==value['coverage'][0]['covered_tokens']==1000
    assert value['coverage'][0]['complete'] and value['coverage'][0]['windows']>1
    assert len(value['vectors'][0])==384 and math.isclose(sum(v*v for v in value['vectors'][0]),1.)

def test_observation_roles_offsets_duplicates_and_source_scopes():
    text='We propose a method. We propose a method. If ready, we show results. A limitation does not vanish. It is defined as X.'
    value=assemble_knowledge('a'*32,'v1','b'*64,[dict(locator='page:1/line:1',text=text)])
    nodes=[n for n in value['nodes'] if n['kind']=='observation']
    assert [n['source_role'] for n in nodes]==['method','method','result','limitation','definition']
    assert len({n['id'] for n in nodes})==5
    for node in nodes:
        assert text[node['char_start']:node['char_end']]==node['text']
        assert node['role_detection']=='heuristic' and node['authority_granted'] is False
    other=assemble_knowledge('c'*32,'v2','d'*64,[dict(locator='page:1/line:1',text=text)])
    assert not {n['id'] for n in nodes}&{n['id'] for n in other['nodes']}

def test_passages_and_formulas_have_actual_source_span_edges():
    value=graph(formula_nodes=[dict(expression='1+1',source_sha256='b'*64,locator='page:1')])
    nodes={n['id']:n for n in value['nodes']}
    mapped=[e for e in value['edges'] if e['kind']=='derived_from_span']
    assert {'passage','formula'}<={nodes[e['source_id']]['kind'] for e in mapped}
    assert all(nodes[e['target_id']]['kind']=='source_span' for e in mapped)


def test_vector_normalization_has_stable_jsonb_zero_representation():
    import json
    from nsai.knowledge import _vector
    result=_vector([2.0,-0.0]+[0.0]*382,384)
    assert result[0]==1.0 and '-0.0' not in json.dumps(result)
