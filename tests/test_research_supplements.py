import copy
import hashlib
import pytest
from nsai import research_store as r,workflow_store as w
from nsai.ingestion import parse_source


@pytest.fixture
def payload(monkeypatch):
    original=b'We propose an efficiency measure. x = 2.';parsed=parse_source(original,'paper.txt');digest=hashlib.sha256(original).hexdigest()
    graph=r.build('a'*32,'v1',parsed)['knowledge']
    extraction=dict(document_id='a'*32,revision='v1',pdf_sha256=digest,source_kind='author_source_tex_not_pdf',authority_granted=False,records=[])
    graph['extraction_evidence_sha256']=r.artifact_hash(extraction)
    passages=[n for n in graph['nodes'] if n['kind']=='passage'];model=dict(name='fixture',sha256='c'*64,revision='d'*40,dimension=384,pooling='token-mean-overlap-compensated-special-mean')
    embeddings=dict(model_identity=model,vectors={n['id']:[1.]+[0.]*383 for n in passages},coverage={n['id']:dict(input_tokens=10,covered_tokens=10,complete=True,max_sequence_length=256,pooling=model['pooling']) for n in passages})
    monkeypatch.setattr(w,'original_source',lambda _: (original,'text/plain'))
    monkeypatch.setattr(r,'get',lambda _:dict(revision='v1'))
    def forbidden():raise AssertionError('Validation must precede all persistence')
    monkeypatch.setattr(r.store,'connect',forbidden)
    return dict(schema_version='nsai.research-supplement/1',kind='author_math',document_id='a'*32,source_sha256=digest,extraction=extraction,knowledge=graph,embeddings=embeddings,memory=None)


@pytest.mark.parametrize('corruption',['digest','document','node-authority','edge-authority','extraction-drift','memory-promotion','partial-tokens','foreign-source'])
def test_untrusted_supplement_cannot_claim_authority_or_wrong_provenance(payload,corruption):
    value=copy.deepcopy(payload)
    if corruption=='digest':value['source_sha256']='f'*64
    if corruption=='document':value['document_id']='b'*32
    if corruption=='node-authority':value['knowledge']['nodes'][0]['authority_granted']=True
    if corruption=='edge-authority':value['knowledge']['edges'][0]['authority_granted']=True
    if corruption=='extraction-drift':value['extraction']['records']=[dict(latex='changed')]
    if corruption=='memory-promotion':value['memory']=dict(canon=[dict(value='true')],authority_granted=True)
    if corruption=='partial-tokens':next(iter(value['embeddings']['coverage'].values()))['complete']=False
    if corruption=='foreign-source':value['knowledge']['source']['revision']='foreign'
    with pytest.raises(ValueError):r.put_supplement('a'*32,value,'local-operator')


def test_search_explicitly_rejects_non_boolean_supplement_activation():
    with pytest.raises(ValueError):r.search([1.]*384,'c'*64,['a'*32],include_supplements='true')
