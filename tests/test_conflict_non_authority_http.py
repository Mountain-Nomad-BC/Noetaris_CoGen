"""HTTP conflict withholding using real retrieval policy and memory projection.

Persistence is substituted; this is not final-image or independent acceptance.
"""
from copy import deepcopy
import pytest
from fastapi.testclient import TestClient
from nsai import api
from nsai.memory import materialize_projection
from nsai.models import conflict_groups


@pytest.mark.parametrize('route',['/v1/chat','/v1/reason'])
@pytest.mark.parametrize('status',['candidate','verified'])
def test_disputed_source_cannot_become_authoritative_answer(monkeypatch,route,status):
    identity={'actor':'local-operator','role':'operator','permissions':['read','chat']}
    monkeypatch.setitem(api.app.dependency_overrides,api.principal,lambda:identity)
    monkeypatch.setattr(api,'principal',lambda authorization:identity)
    monkeypatch.setenv('NSAI_OPERATION_COORDINATION','false')
    hit=dict(id='a'*32,document_id='b'*32,locator='line:1',title='Owned fixture',
             revision='1',original_sha256='c'*64,text='Pump-X operating limit is 85 C.')
    approved=dict(id='approved',document_id=hit['document_id'],locator='line:1',
        subject='Pump-X',predicate='operating limit',value='85 C',status='verified',
        original_sha256='c'*64,reviewed_by='fixture-reviewer')
    other=dict(approved,id='alternative',locator='line:2',value='75 C',status=status)
    claims=[approved,other]
    original=deepcopy(claims)
    memory=materialize_projection([], [approved], [], conflict_groups(claims))
    assert memory['canon']==[] and memory['quarantined']
    monkeypatch.setattr(api.workflows,'begin_invocation',lambda *a:None)
    monkeypatch.setattr(api.workflows,'session',lambda *a:'d'*32)
    monkeypatch.setattr(api.workflows,'memory_context',lambda *a,**k:memory)
    monkeypatch.setattr(api,'library_retrieve',lambda *a,**k:[dict(hit)])
    monkeypatch.setattr(api.workflows,'claim_context',lambda *a,**k:claims)
    def forbidden(*a,**k):pytest.fail('Disputed evidence must not reach inference or review writes')
    for name in ['policy','reserve_inference','review_learning']:
        monkeypatch.setattr(api.workflows,name,forbidden)
    monkeypatch.setattr(api,'admit_source_request',forbidden)
    monkeypatch.setattr(api,'generate_from_sources',forbidden)
    saved=[];finished=[]
    monkeypatch.setattr(api.workflows,'save_exchange',lambda *a,**k:saved.append(a))
    monkeypatch.setattr(api.workflows,'finish_invocation',lambda *a,**k:finished.append((a,k)))
    with TestClient(api.app) as client:
        response=client.post(route,json={'question':'What is Pump-X operating limit?','request_id':'e'*32})
    assert response.status_code==200,response.text
    result=response.json()
    assert result['answer_verified'] is False
    assert result['mode']=='evidence-extract'
    assert result['conflicts'][0]['alternatives'].keys()=={'85 C','75 C'}
    assert 'review required' in result['answer'].lower() or 'review is required' in result['answer'].lower()
    assert result['memory']['canon']==[]
    assert result['memory']['quarantined'][0]['claim_id']=='approved'
    assert len(saved)==len(finished)==1 and not finished[0][1]
    assert claims==original

