"""Owned application HTTP + PostgreSQL + real encoder + real CPU model workflow.

Legacy HTTP authority is exercised; individual-user HTTP admission stays closed.
Synthetic assertions are regression oracles, not held-out semantic acceptance.
"""
import json
import os
from pathlib import Path
import time
from uuid import uuid4
import httpx
from fastapi.testclient import TestClient
from nsai import api,security,store
from semantic_fixture_helpers import configure_authority


def main():
    configure_authority()
    os.environ.update(NSAI_INDEX_WORKER_ENABLED='true',NSAI_INDEX_CONCURRENCY='2')
    operator={'Authorization':'Bearer '+Path(os.environ['NSAI_API_TOKEN_FILE']).read_text().strip()}
    admin={'Authorization':'Bearer '+Path(os.environ['NSAI_ADMIN_TOKEN_FILE']).read_text().strip()}
    alice=security.resolve_principal('Bearer '+Path('/tmp/fixture-user-alice').read_text())
    checks=[];answers=[]
    def check(name,condition):
        if not condition:raise AssertionError(name)
        checks.append(name)
    with httpx.Client(trust_env=False,timeout=2) as model_client:
        for _ in range(120):
            try:
                response=model_client.get('http://llama-cpp:8080/health',headers={
                    'Authorization':'Bearer '+Path(os.environ['NSAI_MODEL_API_KEY_FILE']).read_text().strip()})
                if response.status_code==200:break
            except httpx.HTTPError:pass
            time.sleep(.5)
        else:raise AssertionError('Owned CPU model readiness deadline')
    with TestClient(api.app) as client:
        sources=[]
        for title,text in [('Motor-X original','Motor-X maximum operating temperature is 75 C.'),
                           ('Motor-Y original','Motor-Y maximum operating temperature is 85 C.')]:
            response=client.post('/v1/documents',headers=operator,json=dict(title=title,version='grounded-1',text=text))
            check('HTTP source accepted: '+title,response.status_code==200)
            sources.append(response.json()['document_id'])
        with store.identity_context(alice):
            private=api.ingest(api.DocumentInput(title='Alice private canary',version='private-1',
                text='Motor-Private maximum operating temperature is 99 C. PRIVATE-GROUNDED-CANARY.'),alice)['document_id']
        deadline=time.monotonic()+120
        while time.monotonic()<deadline:
            states=[client.get('/v1/sources/'+doc+'/index',headers=operator) for doc in sources]
            with store.identity_context(alice):private_state=api.source_index(private,alice)
            if all(response.status_code==200 and response.json()['ready'] for response in states) and private_state['ready']:break
            time.sleep(.25)
        else:raise AssertionError('Owned indexed source readiness deadline')
        check('private HTTP gate remains closed',client.get('/v1/documents',headers={'Authorization':'Bearer '+Path('/tmp/fixture-user-alice').read_text()}).status_code==503)
        listed=client.get('/v1/documents',headers=operator)
        check('legacy HTTP library excludes private source',listed.status_code==200 and {row['id'] for row in listed.json()['items']}==set(sources))

        def reason(question,selected,**extra):
            payload=dict(question=question,document_ids=selected,request_id=uuid4().hex,**extra)
            response=client.post('/v1/reason',headers=operator,json=payload)
            print(json.dumps(dict(progress=dict(question=question,status=response.status_code,
                response=response.text[:32000]))),flush=True)
            check('HTTP reasoning returns a bounded response',response.status_code==200)
            result=response.json();answers.append(dict(question=question,result=result))
            check('private canary absent from complete answer envelope','PRIVATE-GROUNDED-CANARY' not in json.dumps(result) and private not in json.dumps(result))
            return payload,result

        payload,first=reason('What is the maximum operating temperature of Motor-X?',[sources[0]])
        check('real model produces grounded original quantity',first['mode']=='model_unverified' and '75' in first['answer'] and first['citation_validation']=='references-resolve')
        check('generation remains explicitly unverified',first['answer_verified'] is False)
        from nsai.answer_support import VERSION
        check('real generated completion carries current support-policy receipt',first['support_policy_version']==VERSION and bool(first['support_claims']))
        check('model call has durable run and audit receipts',bool(first.get('run_id')) and bool(first.get('audit_receipt')))
        check('real tokenizer admitted complete request',first.get('token_admission',{}).get('admitted') is True)
        inspected=client.get('/v1/memory/'+first['session_id'],headers=operator,
            params=[('document_ids',sources[0]),('revision','grounded-1')])
        check('memory inspection preserves explicit question source revision',inspected.status_code==200
            and inspected.json()['source_scope']['document_ids']==[sources[0]]
            and inspected.json()['source_scope']['revision']=='grounded-1')
        before=client.get('/v1/admin/resources',headers=admin).json()
        replay=client.post('/v1/reason',headers=operator,json=payload)
        after=client.get('/v1/admin/resources',headers=admin).json()
        check('idempotent HTTP replay returns original durable run',replay.status_code==200 and replay.json()==first)
        check('idempotent replay does not charge another attempt',before['attempts']==after['attempts'])

        _,switched=reason('What is the maximum operating temperature of Motor-Y?',[sources[1]],session_id=first['session_id'])
        check('explicit source switch produces the new subject quantity',switched['mode']=='model_unverified' and '85' in switched['answer'])
        before=client.get('/v1/admin/resources',headers=admin).json()
        _,missing=reason('Does Motor-Z have an operating temperature, and is it safe?',[sources[0]],session_id=first['session_id'])
        after=client.get('/v1/admin/resources',headers=admin).json()
        check('absent named subject does not reuse old evidence',missing['mode']=='evidence-extract' and not missing['citations'])
        check('insufficient evidence does not reserve a model call',before['attempts']==after['attempts'])

        # Add contradictory evidence only after the positive and subject-switch cases.
        response=client.post('/v1/documents',headers=operator,json=dict(title='Motor-X conflicting revision',version='grounded-2',text='Motor-X maximum operating temperature is 80 C.'))
        check('contradictory fixture source accepted',response.status_code==200)
        conflicting=response.json()['document_id'];deadline=time.monotonic()+120
        while time.monotonic()<deadline:
            status=client.get('/v1/sources/'+conflicting+'/index',headers=operator)
            if status.status_code==200 and status.json()['ready']:break
            time.sleep(.25)
        else:raise AssertionError('Contradictory source readiness deadline')
        before=client.get('/v1/admin/resources',headers=admin).json()
        _,conflict=reason('What is the maximum operating temperature of Motor-X?',[sources[0],conflicting])
        after=client.get('/v1/admin/resources',headers=admin).json()
        check('conflicting evidence withheld from generation',conflict['mode']=='evidence-extract' and bool(conflict['conflicts']))
        check('conflict does not reserve a model call',before['attempts']==after['attempts'])
        check('all charged model calls completed exactly once',after['attempts']==after['completed_inferences']==2)
    print(json.dumps(dict(status='PASS_SCOPED',checks=checks,answers=answers,
        private_http_admitted=False,browser_qualified=False,held_out_quality_accepted=False)))


if __name__=='__main__':main()
