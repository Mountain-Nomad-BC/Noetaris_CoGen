"""Repeated disconnects must not race committed completion into failure receipts."""
import asyncio
from threading import Event
import pytest
from nsai import api


@pytest.mark.parametrize('stage',['inference','exchange','invocation'])
def test_disconnect_waits_for_completion_and_preserves_receipt(monkeypatch,stage):
    run_scenario(monkeypatch,stage,generated=True)


@pytest.mark.parametrize('stage',['exchange','invocation'])
def test_deterministic_response_completion_survives_disconnect(monkeypatch,stage):
    run_scenario(monkeypatch,stage,generated=False)


def run_scenario(monkeypatch,stage,*,generated):
    entered=Event();release=Event();calls=[]
    identity={'actor':'local-operator','role':'operator','permissions':['read','chat']}
    monkeypatch.setenv('NSAI_OPERATION_COORDINATION','false')
    monkeypatch.setattr(api.workflows,'begin_invocation',lambda *a:None)
    monkeypatch.setattr(api.workflows,'session',lambda *a:'a'*32)
    monkeypatch.setattr(api.workflows,'memory_context',lambda *a,**k:{'working':[]})
    hit={'id':'b'*32,'text':'Synthetic source'}
    monkeypatch.setattr(api,'evidence',lambda *a,**k:([hit] if generated else [],[],[],[]))
    monkeypatch.setattr(api.workflows,'policy',lambda:{'inference_enabled':True,'max_output_tokens':64})
    monkeypatch.setattr(api,'require_current_evidence',lambda *a,**k:None)
    monkeypatch.setattr(api,'require_current_claim_context',lambda *a,**k:None)
    monkeypatch.setattr(api,'prepare_source_request',lambda *a,**k:{'max_tokens':64})
    async def admit(*a,**k):return {'admitted':True}
    async def generate(*a,**k):return {'answer':'Synthetic source','mode':'model_unverified','citations':[]}
    monkeypatch.setattr(api,'admit_source_request',admit)
    monkeypatch.setattr(api,'generate_from_sources',generate)
    monkeypatch.setattr(api.workflows,'reserve_inference',lambda *a:('c'*32,64))
    def effect(name,args,kwargs):
        if name==stage:
            entered.set()
            if not release.wait(3):raise TimeoutError('Owned completion fixture deadline')
        calls.append((name,args,kwargs))
        return 'd'*64
    monkeypatch.setattr(api.workflows,'finish_inference',lambda *a,**k:effect('inference',a,k))
    monkeypatch.setattr(api.workflows,'save_exchange',lambda *a,**k:effect('exchange',a,k))
    monkeypatch.setattr(api.workflows,'finish_invocation',lambda *a,**k:effect('invocation',a,k))
    async def scenario():
        task=asyncio.create_task(api.reason(api.Question(question='Synthetic question',request_id='e'*32),identity))
        try:
            assert await asyncio.to_thread(entered.wait,2)
            for _ in range(3):
                task.cancel();await asyncio.sleep(0)
            release.set()
            with pytest.raises(asyncio.CancelledError):await task
        finally:
            release.set()
            if not task.done():
                task.cancel()
                try:await task
                except asyncio.CancelledError:pass
    asyncio.run(scenario())
    expected=['inference','exchange','invocation'] if generated else ['exchange','invocation']
    assert [name for name,_,_ in calls]==expected
    assert all(not kwargs.get('failed') for _,_,kwargs in calls)
    saved=next(args[2] for name,args,_ in calls if name=='exchange')
    final=next(args[2] for name,args,_ in calls if name=='invocation')
    assert saved is final and saved['answer_verified'] is False
    if generated:assert final['audit_receipt']=='d'*64
