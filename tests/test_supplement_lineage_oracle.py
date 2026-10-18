"""Original supplemental mutation fixtures; no paper text or private reference fixtures."""
import importlib.util
import json
from pathlib import Path

import pytest
from nsai.knowledge import assemble_knowledge, memory_projection

spec = importlib.util.spec_from_file_location('supplement_oracle', Path(__file__).resolve().parents[1]/'scripts/validate_research_supplements.py')
oracle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oracle)


@pytest.fixture
def ocr_sample():
    row = dict(document_id='a'*32, revision='r1', source_sha256='b'*64)
    extraction = dict(original_sha256='b'*64, complete=False, pages=[dict(page=1,complete=False)], spans=[dict(locator='page:1:line:1',page=1,text='A measured value requires review.',extraction='ocr')])
    graph = assemble_knowledge('a'*32,'r1','b'*64,[dict(extraction['spans'][0],locator='ocr:page:1:line:1')])
    graph['extraction_kind'] = 'ocr_english_uncalibrated'
    graph['extraction_evidence_sha256'] = oracle.canonical_digest(extraction)
    graph['graph_sha256'] = oracle.canonical_digest({k:v for k,v in graph.items() if k!='graph_sha256'})
    identity = dict(sha256='c'*64)
    ids = [n['id'] for n in graph['nodes'] if n['kind']=='passage']
    embeddings = dict(model_identity=identity,vectors={i:[1.0]+[0.0]*383 for i in ids},coverage={i:dict(input_tokens=10,covered_tokens=10,complete=True) for i in ids})
    supplement = dict(kind='ocr',quality_verified=False,math_recognition_supported=False,processing_complete=False,pages=extraction['pages'],recognized_spans=1)
    return dict(row=row,supplement=supplement,extraction=extraction,graph=graph,embeddings=embeddings,memory=memory_projection(graph),model_identity=identity)


def test_partial_ocr_is_valid_lineage_without_quality_promotion(ocr_sample):
    result = oracle.validate_supplement(**ocr_sample)
    assert result['extraction_complete'] is False
    assert result['passages']==1


def test_rehashed_foreign_namespace_is_rejected(ocr_sample):
    graph = ocr_sample['graph']
    node = next(n for n in graph['nodes'] if n['kind']=='source_span')
    node['locator'] = 'page:1:line:1'
    graph['graph_sha256'] = oracle.canonical_digest({k:v for k,v in graph.items() if k!='graph_sha256'})
    with pytest.raises(ValueError,match='Unanchored native node'):
        oracle.validate_supplement(**ocr_sample)


def test_extraction_graph_content_mismatch_is_rejected(ocr_sample):
    ocr_sample['extraction']['spans'][0]['text']='Altered extraction'
    with pytest.raises(ValueError,match='extraction content binding'):
        oracle.validate_supplement(**ocr_sample)


def test_false_ocr_quality_claim_is_rejected(ocr_sample):
    ocr_sample['supplement']['quality_verified']=True
    with pytest.raises(ValueError,match='quality claim'):
        oracle.validate_supplement(**ocr_sample)


def test_partial_ocr_cannot_claim_complete(ocr_sample):
    ocr_sample['supplement']['processing_complete']=True
    with pytest.raises(ValueError,match='completeness claim'):
        oracle.validate_supplement(**ocr_sample)


def test_author_pdf_only_has_no_fabricated_graph():
    row=dict(document_id='a'*32,revision='r1',source_sha256='b'*64)
    extraction=dict(document_id='a'*32,revision='r1',pdf_sha256='b'*64,authority_granted=False,pdf_alignment='not_verified',source_archive_sha256='d'*64,processing_complete=False,records=[])
    supplement=dict(kind='author_math',pdf_alignment='not_verified',source_archive_sha256='d'*64,processing_complete=False,formula_candidates=0)
    result=oracle.validate_supplement(row,supplement,extraction,None,None,None,{})
    assert result['graph_available'] is False
    with pytest.raises(ValueError,match='Empty extraction'):
        oracle.validate_supplement(row,supplement,extraction,{},None,None,{})


@pytest.fixture
def mapping_sample():
    model=dict(sha256='e'*64)
    ids=['a','b','c','d','e']
    vectors={i:[float(n==position) for n in range(384)] for position,i in enumerate(ids)}
    manifest=dict(papers=[dict(document_id=i,source_sha256=i*64) for i in ids],semantic_model=model)
    semantics=dict(model_identity=model,vectors=vectors)
    edges=[]
    for left in ids:
        for right in sorted((i for i in ids if i!=left),reverse=True)[:3]:
            edges.append(dict(source_id=left,target_id=right,cosine=0.0,model_sha256='e'*64,kind='semantic_neighbour_candidate',authority_granted=False,entailment_verified=False))
    mapping=dict(authority_granted=False,model_identity=model,nodes=[dict(id=i,source_sha256=i*64) for i in ids],edges=edges)
    source_vectors={i:({'passage':v},{'passage':dict(input_tokens=2)}) for i,v in vectors.items()}
    return dict(manifest=manifest,mapping=mapping,semantics=semantics,document_vectors=source_vectors)


def test_independent_orthogonal_map(mapping_sample):
    assert oracle.validate_map(**mapping_sample)==dict(documents=5,edges=15)


def test_invented_similarity_is_rejected(mapping_sample):
    mapping_sample['mapping']['edges'][0]['cosine']=0.5
    with pytest.raises(ValueError,match='cosine mismatch'):
        oracle.validate_map(**mapping_sample)


def test_replaced_centroid_is_rejected(mapping_sample):
    mapping_sample['semantics']['vectors']['a']=[0.0,1.0]+[0.0]*382
    with pytest.raises(ValueError,match='centroid derivation'):
        oracle.validate_map(**mapping_sample)


def test_missing_neighbour_is_rejected(mapping_sample):
    mapping_sample['mapping']['edges'].pop()
    with pytest.raises(ValueError,match='nearest neighbours'):
        oracle.validate_map(**mapping_sample)


@pytest.mark.parametrize('actual',[[],['author_math'],['ocr']])
def test_missing_expected_supplements_are_rejected(actual):
    with pytest.raises(ValueError,match='Expected supplement inventory'):
        oracle.validate_inventory(dict(pages_requiring_ocr=[2]),actual,author_expected=True)


def test_native_only_document_does_not_require_ocr():
    oracle.validate_inventory(dict(pages_requiring_ocr=[]),['author_math'],author_expected=True)
