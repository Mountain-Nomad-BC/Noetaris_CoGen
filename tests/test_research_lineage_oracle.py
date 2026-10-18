"""Mutation tests exercise an independent oracle, including correctly rehashed bad graphs."""
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from nsai.knowledge import assemble_knowledge, memory_projection

spec = importlib.util.spec_from_file_location('lineage_oracle', Path(__file__).resolve().parents[1] / 'scripts/validate_research_lineage.py')
oracle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oracle)


def rehash(graph):
    raw = json.dumps({k:v for k,v in graph.items() if k != 'graph_sha256'}, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode()
    graph['graph_sha256'] = hashlib.sha256(raw).hexdigest()


@pytest.fixture
def sample():
    span = dict(locator='page:1:line:1', page=1, text='Measured value x = 3. No safe conclusion without a second measurement.')
    graph = assemble_knowledge('a'*32, 'r1', 'b'*64, [span])
    passages = [n['id'] for n in graph['nodes'] if n['kind'] == 'passage']
    identity = dict(sha256='c'*64)
    return dict(parsed=dict(original_sha256='b'*64, spans=[span]), graph=graph,
                formulas=dict(document_id='a'*32, revision='r1', original_sha256='b'*64, records=[]),
                embeddings=dict(model_identity=identity, vectors={p:[1.0]+[0.0]*383 for p in passages}, coverage={p:dict(input_tokens=20, covered_tokens=20, complete=True) for p in passages}),
                memory=memory_projection(graph), document_id='a'*32, revision='r1', original_sha256='b'*64, model_identity=identity)


def test_original_source_lineage_passes(sample):
    result = oracle.validate_document(**sample)
    assert result['passages'] == 1


def test_rehashed_dangling_edge_fails(sample):
    sample['graph']['edges'][0]['target_id'] = 'missing'
    rehash(sample['graph'])
    with pytest.raises(ValueError, match='Dangling edge'):
        oracle.validate_document(**sample)


def test_rehashed_invented_quote_fails(sample):
    node = next(n for n in sample['graph']['nodes'] if n['kind'] == 'observation')
    node['text'] = 'Invented claim'
    rehash(sample['graph'])
    with pytest.raises(ValueError, match='Observation quote'):
        oracle.validate_document(**sample)


def test_missing_embedding_fails(sample):
    sample['embeddings']['vectors'].clear()
    with pytest.raises(ValueError, match='bijection'):
        oracle.validate_document(**sample)


def test_incomplete_token_coverage_fails(sample):
    next(iter(sample['embeddings']['coverage'].values()))['covered_tokens'] = 19
    with pytest.raises(ValueError, match='Token coverage'):
        oracle.validate_document(**sample)


def test_canon_promotion_fails(sample):
    sample['memory']['canon'] = ['unreviewed']
    with pytest.raises(ValueError, match='Memory authority'):
        oracle.validate_document(**sample)


def test_nonfinite_vector_fails(sample):
    next(iter(sample['embeddings']['vectors'].values()))[0] = float('nan')
    with pytest.raises(ValueError, match='Invalid vector'):
        oracle.validate_document(**sample)


def test_foreign_edge_provenance_fails(sample):
    sample['graph']['edges'][0]['provenance'] = dict(document_id='d'*32)
    rehash(sample['graph'])
    with pytest.raises(ValueError, match='Edge provenance'):
        oracle.validate_document(**sample)


def test_rehashed_missing_passage_with_matching_empty_index_fails(sample):
    graph = sample['graph']
    removed = {n['id'] for n in graph['nodes'] if n['kind'] == 'passage'}
    graph['nodes'] = [n for n in graph['nodes'] if n['id'] not in removed]
    graph['edges'] = [e for e in graph['edges'] if e['source_id'] not in removed and e['target_id'] not in removed]
    sample['embeddings']['vectors'].clear()
    sample['embeddings']['coverage'].clear()
    rehash(graph)
    with pytest.raises(ValueError, match='Passage source coverage'):
        oracle.validate_document(**sample)
