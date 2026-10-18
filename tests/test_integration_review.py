"""Independent review regressions from original synthetic counterexamples; no live operations."""
from copy import deepcopy
import hashlib
import asyncio
from threading import Event
import httpx
import pytest
from nsai.ingestion import parse_source, validate_parsed_source
from nsai.inference import factual_support


def test_model_quantity_cannot_transfer_between_entities_in_same_cited_excerpt():
    hits = [{'text':'Pump-A maximum operating temperature is 85 C.\nPump-B maximum operating temperature is 75 C.'}]
    assert factual_support('Pump-A maximum operating temperature is 85 C.',hits)
    assert not factual_support('Pump-A maximum operating temperature is 75 C.',hits)


def test_parser_cannot_forge_plain_source_span_with_correct_original_hash_and_raw_text():
    original=b'Pump-A maximum operating temperature is 85 C.'
    parsed=deepcopy(parse_source(original,'source.txt'))
    forged='Pump-A maximum operating temperature is 75 C.'
    parsed['spans'][0]['text']=forged
    parsed['normalization_map'][0]['raw_text']=forged
    parsed['normalization_map'][0]['normalized_text']=forged
    parsed['chunks'][0]['text']=forged
    parsed['chunks'][0]['sha256']=hashlib.sha256(forged.encode()).hexdigest()
    # The source bytes, source hash and raw_text deliberately remain authentic.
    with pytest.raises(ValueError): validate_parsed_source(original,parsed)


def test_complete_parser_result_requires_searchable_chunk_coverage():
    original=b'Original native text that must remain searchable.'
    parsed=deepcopy(parse_source(original,'source.txt'))
    parsed['chunks']=[]
    with pytest.raises(ValueError): validate_parsed_source(original,parsed)


def test_normalization_lineage_must_cover_every_span_once():
    original=b'First native line.\nSecond native line.'
    parsed=deepcopy(parse_source(original,'source.txt'))
    parsed['normalization_map'][1]=deepcopy(parsed['normalization_map'][0])
    with pytest.raises(ValueError): validate_parsed_source(original,parsed)


def test_disabled_inference_does_not_send_source_to_model_tokenizer(monkeypatch):
    from fastapi.testclient import TestClient
    from nsai import api
    identity={'actor':'local-operator','role':'operator','permissions':['read','chat']}
    principal=api.principal
    previous=dict(api.app.dependency_overrides)
    api.app.dependency_overrides[principal]=lambda:identity
    monkeypatch.setattr(api,'principal',lambda authorization:identity)
    monkeypatch.setenv('NSAI_CENTRAL_SECURITY_ENABLED','false')
    monkeypatch.setattr(api.workflows,'session',lambda *a,**k:'a'*32)
    monkeypatch.setattr(api.workflows,'memory_context',lambda *a,**k:{'working':[]})
    monkeypatch.setattr(api,'evidence',lambda *a,**k:([{'id':'b'*32,'text':'Original source.'}],[],[],[]))
    monkeypatch.setattr(api.workflows,'policy',lambda:{'inference_enabled':False,'max_output_tokens':64})
    monkeypatch.setattr(api,'prepare_source_request',lambda *a,**k:{'max_tokens':64})
    calls=[]
    async def tokenizer(body):
        calls.append(body);return {'admitted':True}
    monkeypatch.setattr(api,'admit_source_request',tokenizer)
    def disabled(*args): raise PermissionError('Inference disabled by local administrator')
    monkeypatch.setattr(api.workflows,'reserve_inference',disabled)
    try:
        with TestClient(api.app) as client:
            response=client.post('/v1/reason',json={'question':'What is the source?'})
        assert response.status_code==403
        assert calls==[], 'Disabled policy still invoked model tokenizer with source material'
    finally:
        api.app.dependency_overrides.clear();api.app.dependency_overrides.update(previous)


@pytest.mark.parametrize('failure_stage',['token-admission','completion'])
def test_provider_failure_is_generic_and_durably_fails_admitted_work(monkeypatch,failure_stage):
    from fastapi.testclient import TestClient
    from nsai import api

    identity={'actor':'local-operator','role':'operator','permissions':['read','chat']}
    previous=dict(api.app.dependency_overrides)
    api.app.dependency_overrides[api.principal]=lambda:identity
    monkeypatch.setattr(api,'principal',lambda authorization:identity)
    monkeypatch.setenv('NSAI_OPERATION_COORDINATION','false')
    monkeypatch.setattr(api.workflows,'begin_invocation',lambda *args:None)
    monkeypatch.setattr(api.workflows,'session',lambda *args:'a'*32)
    monkeypatch.setattr(api.workflows,'memory_context',lambda *args,**kwargs:{'working':[]})
    hit=dict(id='b'*32,text='Pump-A maximum operating temperature is 85 C.')
    monkeypatch.setattr(api,'evidence',lambda *args,**kwargs:([hit],[],[],[]))
    monkeypatch.setattr(api.workflows,'policy',lambda:{'inference_enabled':True,'max_output_tokens':64})
    monkeypatch.setattr(api,'require_current_evidence',lambda *args,**kwargs:None)
    monkeypatch.setattr(api,'require_current_claim_context',lambda *args,**kwargs:None)
    monkeypatch.setattr(api,'prepare_source_request',lambda *args,**kwargs:{
        'messages':[{'role':'user','content':'question'}],'max_tokens':64})
    async def admit(_body):
        if failure_stage=='token-admission':
            raise httpx.ReadTimeout('provider-private-response-must-not-leak')
        return {'admitted':True}
    monkeypatch.setattr(api,'admit_source_request',admit)

    reservations=[]
    if failure_stage=='token-admission':
        monkeypatch.setattr(api.workflows,'reserve_inference',
            lambda *args:pytest.fail('Token-admission failure must precede reservation'))
    else:
        monkeypatch.setattr(api.workflows,'reserve_inference',lambda *args:('c'*32,64))
        async def complete(*args,**kwargs):
            raise httpx.ReadTimeout('provider-private-response-must-not-leak')
        monkeypatch.setattr(api,'generate_from_sources',complete)
        def finish_inference(*args,**kwargs):
            reservations.append((args,kwargs))
        monkeypatch.setattr(api.workflows,'finish_inference',finish_inference)

    invocation_failures=[]
    monkeypatch.setattr(api.workflows,'finish_invocation',
        lambda *args,**kwargs:invocation_failures.append((args,kwargs)))
    try:
        with TestClient(api.app) as client:
            response=client.post('/v1/reason',json={
                'question':'What is Pump-A temperature?',
                'request_id':'d'*32,
            })
        assert response.status_code==502
        assert response.json()=={'detail':'Inference unavailable; inspect model status'}
        assert 'provider-private-response-must-not-leak' not in response.text
        assert len(invocation_failures)==1
        assert invocation_failures[0][0][1:]==('d'*32,{'error_type':'ReadTimeout'})
        assert invocation_failures[0][1]=={'failed':True}
        if failure_stage=='completion':
            assert len(reservations)==1
            assert reservations[0][0][0:2]==('c'*32,'local-operator')
            assert reservations[0][1]=={'failed':True}
    finally:
        api.app.dependency_overrides.clear();api.app.dependency_overrides.update(previous)


def test_cancellation_during_inference_reservation_fails_the_committed_run(monkeypatch):
    from nsai import api

    identity={'actor':'local-operator','role':'operator','permissions':['read','chat']}
    monkeypatch.setenv('NSAI_OPERATION_COORDINATION','false')
    monkeypatch.setattr(api.workflows,'begin_invocation',lambda *args:None)
    monkeypatch.setattr(api.workflows,'session',lambda *args:'a'*32)
    monkeypatch.setattr(api.workflows,'memory_context',lambda *args,**kwargs:{'working':[]})
    monkeypatch.setattr(api,'evidence',lambda *args,**kwargs:([{'id':'b'*32,'text':'Source.'}],[],[],[]))
    monkeypatch.setattr(api.workflows,'policy',lambda:{'inference_enabled':True,'max_output_tokens':64})
    monkeypatch.setattr(api,'require_current_evidence',lambda *args,**kwargs:None)
    monkeypatch.setattr(api,'require_current_claim_context',lambda *args,**kwargs:None)
    monkeypatch.setattr(api,'prepare_source_request',lambda *args,**kwargs:{
        'messages':[{'role':'user','content':'question'}],'max_tokens':64})
    async def admit(_body):return {'admitted':True}
    monkeypatch.setattr(api,'admit_source_request',admit)

    reserve_entered=Event();allow_reserve_to_commit=Event()
    def reserve(*args):
        reserve_entered.set()
        if not allow_reserve_to_commit.wait(3):raise TimeoutError('Reservation fixture timed out')
        return 'c'*32,64
    monkeypatch.setattr(api.workflows,'reserve_inference',reserve)
    failures=[]
    finish_entered=Event();allow_finish_to_commit=Event()
    def finish_inference(*args,**kwargs):
        finish_entered.set()
        if not allow_finish_to_commit.wait(3):raise TimeoutError('Finalization fixture timed out')
        failures.append(('inference',args,kwargs))
    monkeypatch.setattr(api.workflows,'finish_inference',finish_inference)
    monkeypatch.setattr(api.workflows,'finish_invocation',
        lambda *args,**kwargs:failures.append(('invocation',args,kwargs)))

    async def scenario():
        task=asyncio.create_task(api.reason(
            api.Question(question='What is in the source?',request_id='d'*32),identity))
        assert await asyncio.to_thread(reserve_entered.wait,2)
        task.cancel()
        await asyncio.sleep(0)
        task.cancel()
        allow_reserve_to_commit.set()
        assert await asyncio.to_thread(finish_entered.wait,2)
        task.cancel()
        allow_finish_to_commit.set()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(scenario())
    assert [failure[0] for failure in failures]==['inference','invocation']
    assert failures[0][1][0:2]==('c'*32,'local-operator')
    assert failures[0][1][2]=={'error_type':'CancelledError'}
    assert failures[0][2]=={'failed':True}
    assert failures[1][1][1:]==('d'*32,{'error_type':'CancelledError'})
    assert failures[1][2]=={'failed':True}


def test_cancellation_during_invocation_admission_fails_the_pending_receipt(monkeypatch):
    from nsai import api

    identity={'actor':'local-operator','role':'operator','permissions':['read','chat']}
    monkeypatch.setenv('NSAI_OPERATION_COORDINATION','false')
    begin_entered=Event();allow_begin_to_commit=Event()
    def begin(*args):
        begin_entered.set()
        if not allow_begin_to_commit.wait(3):raise TimeoutError('Invocation fixture timed out')
        return None
    monkeypatch.setattr(api.workflows,'begin_invocation',begin)
    failures=[]
    monkeypatch.setattr(api.workflows,'finish_invocation',
        lambda *args,**kwargs:failures.append((args,kwargs)))

    async def scenario():
        task=asyncio.create_task(api.reason(
            api.Question(question='What is in the source?',request_id='d'*32),identity))
        assert await asyncio.to_thread(begin_entered.wait,2)
        task.cancel()
        await asyncio.sleep(0)
        task.cancel()
        allow_begin_to_commit.set()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(scenario())
    assert len(failures)==1
    assert failures[0][0][0:2]==('local-operator','d'*32)
    assert failures[0][0][2]=={'error_type':'CancelledError'}
    assert failures[0][1]=={'failed':True}


def test_reason_rejects_claim_context_changed_during_generation(monkeypatch):
    from fastapi import HTTPException
    from nsai import api

    identity={'actor':'local-operator','role':'operator','permissions':['read','chat']}
    monkeypatch.setenv('NSAI_OPERATION_COORDINATION','false')
    hit=dict(id='b'*32,document_id='doc',locator='line:1',text='Pump-A operating limit is 85 C.')
    initial=[dict(id='claim-a',subject='pump-a',predicate='operating limit',value='85 C',
        document_id='doc',locator='line:1',status='candidate')]
    current=[*initial,dict(id='claim-b',subject='pump-a',predicate='operating limit',value='90 C',
        document_id='other',locator='line:9',status='candidate')]
    monkeypatch.setattr(api.workflows,'begin_invocation',lambda *args:None)
    monkeypatch.setattr(api.workflows,'session',lambda *args:'a'*32)
    monkeypatch.setattr(api.workflows,'memory_context',lambda *args,**kwargs:{'working':[]})
    monkeypatch.setattr(api,'evidence',lambda *args,**kwargs:( [hit],initial,[],[]))
    contexts=[initial,current]
    monkeypatch.setattr(api.workflows,'claim_context',
        lambda *args,**kwargs:contexts.pop(0) if contexts else current)
    monkeypatch.setattr(api.workflows,'policy',lambda:{'inference_enabled':True,'max_output_tokens':64})
    monkeypatch.setattr(api,'require_current_evidence',lambda *args,**kwargs:None)
    monkeypatch.setattr(api,'prepare_source_request',lambda *args,**kwargs:{
        'messages':[{'role':'user','content':'question'}],'max_tokens':64})
    async def admit(_body):return {'admitted':True}
    generated=[]
    async def generate(*args,**kwargs):
        generated.append(True)
        return {'mode':'model_unverified','answer':'85 C','citations':[]}
    monkeypatch.setattr(api,'admit_source_request',admit)
    monkeypatch.setattr(api,'generate_from_sources',generate)
    finalized=[];saved=[];invocations=[]
    monkeypatch.setattr(api.workflows,'reserve_inference',lambda *args:('c'*32,64))
    monkeypatch.setattr(api.workflows,'finish_inference',
        lambda *args,**kwargs:finalized.append((args,kwargs)))
    monkeypatch.setattr(api.workflows,'save_exchange',lambda *args,**kwargs:saved.append(args))
    monkeypatch.setattr(api.workflows,'finish_invocation',
        lambda *args,**kwargs:invocations.append((args,kwargs)))

    with pytest.raises(HTTPException) as failure:
        asyncio.run(api.reason(api.Question(question='What is Pump-A limit?',request_id='d'*32),identity))
    assert failure.value.status_code==409
    assert generated==[True]
    assert finalized and finalized[0][1]=={'failed':True}
    assert saved==[]
    assert invocations and invocations[0][1]=={'failed':True}


@pytest.mark.parametrize('value',['yes','true','approved',1,0,None])
def test_governed_approval_requires_json_boolean_not_natural_language(value):
    from nsai.api import ActionApproval
    with pytest.raises(ValueError): ActionApproval(approve=value)


def check_postgres_central_fail_closed(conn):
    """Root's owned PostgreSQL runner invokes this; every case force-rolls back its savepoint."""
    import json
    from psycopg.errors import CheckViolation
    outcomes=[]
    cases=[('missing-enabled',{}),('json-null',None),('string-false',{'enabled':'false'}),
           ('boolean-true',{'enabled':True}),('numeric-zero',{'enabled':0}),('array',[])]
    for name, configuration in cases:
        rejected=False
        try:
            with conn.transaction(force_rollback=True):
                conn.execute('UPDATE local_policy SET central_config=%s::jsonb WHERE id=1',(json.dumps(configuration),))
        except CheckViolation:
            rejected=True
        assert rejected, f'PostgreSQL admitted invalid central configuration: {name}'
        outcomes.append({'case':name,'status':'PASS','expected':'check violation'})
    with conn.transaction(force_rollback=True):
        row=conn.execute('UPDATE local_policy SET central_config=%s::jsonb WHERE id=1 RETURNING central_config',
                         (json.dumps({'enabled':False}),)).fetchone()
        assert row and row[0].get('enabled') is False
    outcomes.append({'case':'typed-disabled','status':'PASS','expected':'accepted within rollback savepoint'})
    return outcomes


def migration_module():
    import importlib.util
    from pathlib import Path
    spec=importlib.util.spec_from_file_location('migration_review',Path(__file__).resolve().parents[1]/'scripts/migrate.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


@pytest.mark.parametrize('password',["x'*32; DROP ROLE nsai_app; --",'x'*31,'é'*32,'x'*1025,'x'*31+'\n'])
def test_role_sql_rejects_injection_nonascii_or_unbounded_password(password):
    with pytest.raises(ValueError): migration_module().role_sql(password)


def test_role_sql_is_shared_convergent_contract_for_all_active_tables():
    sql=migration_module().role_sql('synthetic_'+('x'*40))
    assert sql.endswith('COMMIT;\n')
    assert 'COMMIT;' not in migration_module().role_sql('synthetic_'+('x'*40),include_commit=False)
    assert 'GRANT SELECT,INSERT ON governed_records,governed_reviews,policy_actions,invocation_receipts' in sql
    assert 'GRANT UPDATE(state,approved_by,receipt_sha256) ON policy_actions' in sql
    assert sql.index('REVOKE ALL ON ALL TABLES')<sql.index('GRANT SELECT,INSERT ON governed_records')
    assert 'NOBYPASSRLS' in sql and 'pg_auth_members' in sql
