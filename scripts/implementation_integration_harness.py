from psycopg.errors import CheckViolation, RaiseException, InsufficientPrivilege
"""Executed inside an owned candidate container against an owned PostgreSQL DB."""
import os,json,hashlib,threading,time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import httpx
from fastapi.testclient import TestClient
from nsai import api,store,workflow_store as w,inference,parser
from nsai.ingestion import parse_source


def main():

    checks=[]
    def check(name,condition,details=None):
        checks.append(dict(name=name,status='PASS' if condition else 'FAIL',details=details))
        if not condition:
            print(json.dumps(checks[-1],default=str),file=__import__('sys').stderr)
            raise AssertionError(name)

    for role,setting in api.__dict__.get('FILES',{}).items():pass
    from nsai.security import FILES
    for role,setting in FILES.items():
        p=Path('/tmp/'+role);p.write_text('synthetic-'+role+'x'*48);os.environ[setting]=str(p)
    def auth(role='operator'):return {'Authorization':'Bearer '+'synthetic-'+role+'x'*48}
    os.environ.update(NSAI_MODEL_URL='http://llama-cpp:8080/v1',NSAI_MODEL_NAME='synthetic',NSAI_PARSER_URL='http://parser:8788')
    p=Path('/tmp/parser');p.write_text('synthetic-parser'+'x'*48);os.environ['NSAI_PARSER_TOKEN_FILE']=str(p)
    os.environ.pop('NSAI_MODEL_API_KEY_FILE',None)
    actual_async=httpx.AsyncClient
    parser_client=TestClient(parser.app,raise_server_exceptions=False)
    def transport(request):
        if request.url.host=='parser':
            response=parser_client.post('/parse',content=request.content,headers=dict(request.headers))
            return httpx.Response(response.status_code,content=response.content)
        if request.url.path.endswith('/models'):return httpx.Response(200,json={'data':[{'id':'synthetic'}]})
        if request.url.path=='/props':return httpx.Response(200,json={'default_generation_settings':{'n_ctx':4096}})
        if request.url.path=='/apply-template':return httpx.Response(200,json={'prompt':'independent synthetic template'})
        if request.url.path=='/tokenize':return httpx.Response(200,json={'tokens':[1]*100})
        request_body=json.loads(request.content)
        import re
        identifier=re.findall(r'\[([a-f0-9]{32})\]',request_body['messages'][1]['content'])[0]
        return httpx.Response(200,json={'choices':[{'message':{'content':json.dumps(dict(answer='Pump-X operating limit is 85 C',citation_ids=[identifier]))}}],'usage':{'completion_tokens':20}})
    httpx.AsyncClient=lambda **kw:actual_async(transport=httpx.MockTransport(transport),**kw)
    client=TestClient(api.app,raise_server_exceptions=False)
    with client:
        for path in ['/healthz','/readyz','/','/assets/app.js']:
            check('readiness '+path,client.get(path).status_code==200)
        for role in FILES:
            check('execution remains denied '+role,client.post('/v1/execute',headers=auth(role)).status_code==403)
        response=client.get('/v1/claims',headers=[(b'authorization',b'Bearer \xff')])
        check('nonASCII bearer 401 with headers',response.status_code==401 and response.headers['cache-control']=='no-store')
        check('viewer ingest denied',client.post('/v1/documents',headers=auth('viewer'),json=dict(title='x',text='x')).status_code==403)
        docs=[]
        for version,value in [('1','85'),('2','75')]:
            response=client.post('/v1/documents',headers=auth(),json=dict(title='Synthetic',text=f'Pump-X operating limit is {value} C',version=version))
            check('ingest '+version,response.status_code==200,response.json())
            docs.append(response.json()['document_id'])
        r=client.post('/v1/chat',headers=auth(),json=dict(question='What are Pump-X operating limits?'))
        check('retrieval alternate and global conflict',r.status_code==200 and len(r.json()['conflicts'])==1)
        scoped=client.post('/v1/chat',headers=auth(),json=dict(question='Pump-X',document_ids=[docs[0]],revision='1'))
        check('document scope excludes other revision',scoped.status_code==200 and not scoped.json()['conflicts'] and all(c['document_id']==docs[0] for c in scoped.json()['citations']))
        check('stale scope denied',client.post('/v1/chat',headers=auth(),json=dict(question='Pump-X',document_ids=[docs[0]],revision='bad')).status_code==409)
        original=client.get('/v1/sources/'+docs[0]+'/original',headers=auth('viewer'))
        check('safe exact original',original.content==b'Pump-X operating limit is 85 C' and original.headers['content-type'].startswith('text/plain'))
        items=client.get('/v1/claims',headers=auth()).json()['items']
        chosen=next(c for c in items if c['document_id']==docs[0])
        review=client.post('/v1/review/'+chosen['id'],headers=auth('reviewer'),json=dict(decision='accept',expected_revision=1,rationale='Original synthetic independent review'))
        check('independent review',review.status_code==200)
        reason=client.post('/v1/reason',headers=auth(),json=dict(question='Pump-X',document_ids=[docs[0]]))
        check('mock admitted reason',reason.status_code==200 and reason.json()['token_admission']['admitted'] and reason.json()['answer_verified'] is False,reason.json())
        new=w.persist_source('Synthetic new','3',b'Pump-X operating limit is 95 C',parse_source(b'Pump-X operating limit is 95 C','new.txt'),'local-operator')
        reflection=w.reflect_on_conflicts('local-operator')
        check('reviewed plus new conflict reflection',reflection['created']>=1)
        blocked=client.post('/v1/reason',headers=auth(),json=dict(question='Pump-X'))
        check('conflict model call withheld',blocked.status_code==200 and blocked.json()['mode']=='evidence-extract' and blocked.json()['conflicts'])
        memory=w.memory_context('local-operator',scoped.json()['session_id'],'Pump-X')
        check('conflicting canon quarantined',not memory['canon'] and bool(memory['quarantined']))
        check('memory full envelope within budget',len(json.dumps(memory,ensure_ascii=False).encode())<=16384)
        check('cross actor session denied',client.get('/v1/memory/'+memory['plan']['subject_id'],headers=auth('admin')).status_code==403)
        run,budget=w.reserve_inference('local-operator')
        with ThreadPoolExecutor(max_workers=4) as pool:
            receipts=list(pool.map(lambda _:w.finish_inference(run,'local-operator',dict(probe='race')),range(4)))
        check('settlement idempotent under real concurrent DB locks',len(set(receipts))==1)
        with store.connect() as conn:
            events=conn.execute("SELECT count(*) FROM audit_events WHERE details->>'run_id'=%s",(run,)).fetchone()[0]
            check('one settlement event',events==1)
        try:w.finish_inference(run,'foreign',{})
        except PermissionError:check('foreign finish denied',True)
        else:check('foreign finish denied',False)
        reservation,unused=w.reserve_inference('local-operator')
        # Owned test database only, application role cannot alter created_at.
        check('local audit chain valid',w.audit_report()['valid'])
        try:
            with store.connect() as conn:conn.execute("UPDATE local_policy SET central_config='{"+'"enabled":true'+"}'::jsonb")
        except CheckViolation:check('DB central enable denied',True)
        else:check('DB central enable denied',False)
        try:
            with store.connect() as conn:conn.execute("UPDATE documents SET title='overwrite'")
        except (RaiseException,InsufficientPrivilege):check('original mutation denied',True)
        else:check('original mutation denied',False)
        # Sustained bounded read concurrency against the real pooled collaborator.
        started=time.monotonic()
        with ThreadPoolExecutor(max_workers=8) as pool:
            results=list(pool.map(lambda _:len(store.all_claims()),range(80)))
        check('bounded pooled concurrent reads',all(n==3 for n in results),dict(requests=80,seconds=time.monotonic()-started))
        for invalid in [{},None,dict(enabled='false'),dict(enabled=True)]:
            try:
                with store.connect() as conn:conn.execute('UPDATE local_policy SET central_config=%s::jsonb',(json.dumps(invalid),))
            except CheckViolation:check('central invalid shape denied '+json.dumps(invalid),True)
            else:check('central invalid shape denied '+json.dumps(invalid),False)
        assembled=client.post('/v1/assembly/'+docs[0],headers=auth())
        check('persistent sourcebound assembly',assembled.status_code==200 and assembled.json()['authority_granted'] is False,assembled.json())
        record_id=assembled.json()['id']
        check('independent governed review',client.post('/v1/governed/records/'+record_id+'/review',headers=auth('reviewer'),json=dict(decision='reviewed',rationale='Independent sourcebound assembly review')).status_code==200)
        check('governed review retry denied',client.post('/v1/governed/records/'+record_id+'/review',headers=auth('reviewer'),json=dict(decision='reviewed',rationale='Independent sourcebound assembly review')).status_code==409)
        text='Motor stops when hot.\nObserved 85 C at the sensor.\nSuspect poor cooling.\nCheck airflow?'
        issue_doc=w.persist_source('Engineering issue synthetic','1',text.encode(),parse_source(text.encode(),'issue.txt'),'local-operator')['document_id']
        issue=client.post('/v1/issues/analyze',headers=auth(),json=dict(document_id=issue_doc))
        check('persistent engineering issue flow',issue.status_code==200 and issue.json()['payload']['diagnosis_verified'] is False and len(issue.json()['payload']['nodes'])==4,issue.json())
        proposal=client.post('/v1/governed/proposals',headers=auth(),json=dict(document_id=docs[0],capability='alias-proposal',data={'alias':'temperature','target':'operating limit'}))
        check('dataonly proposal',proposal.status_code==200 and proposal.json()['authority_granted'] is False)
        forged=client.post('/v1/governed/proposals',headers=auth(),json=dict(document_id=docs[0],capability='alias-proposal',data={'enabled':True}))
        check('proposal authority denied',forged.status_code==409)
        current=w.policy()
        desired=dict(expected_revision=current['revision'],inference_enabled=current['inference_enabled'],daily_call_limit=current['daily_call_limit']+1,max_output_tokens=current['max_output_tokens'],central_config={'enabled':False,'provider':'none','issuer':None})
        staged=client.put('/v1/admin/policy',headers=auth('admin'),json=desired)
        check('increased policy staged not applied',staged.status_code==200 and staged.json()['policy_unchanged'] and w.policy()['revision']==current['revision'],staged.json())
        action_id=staged.json()['action_id']
        same_actor=client.post('/v1/admin/actions/'+action_id+'/review',headers=auth('admin'),json={'approve':True})
        check('same actor policy approval denied',same_actor.status_code==403,dict(status=same_actor.status_code,body=same_actor.text))
        applied=client.post('/v1/admin/actions/'+action_id+'/review',headers=auth('reviewer'),json={'approve':True})
        check('independent policy approval applied',applied.status_code==200 and applied.json()['state']=='applied')
        check('policy approval retry idempotent',client.post('/v1/admin/actions/'+action_id+'/review',headers=auth('reviewer'),json={'approve':True}).json()['idempotent'])
        check('retention never deletes',client.get('/v1/admin/retention',headers=auth('admin')).json()['delete_enabled'] is False)
        replay_payload=dict(question='Pump-X',document_ids=[docs[0]],request_id='e'*32)
        first=client.post('/v1/chat',headers=auth(),json=replay_payload)
        second=client.post('/v1/chat',headers=auth(),json=replay_payload)
        check('durable invocation replay preserves one exchange',first.status_code==200 and second.json()==first.json())
        changed=client.post('/v1/chat',headers=auth(),json=dict(replay_payload,question='Different request'))
        check('idempotency key cannot rebind payload',changed.status_code==409)
        reparse=client.post('/v1/sources/'+docs[0]+'/reparse',headers=auth())
        check('same original independent extraction generation',reparse.status_code==200 and not reparse.json()['payload']['active'])
        detail=client.get('/v1/governed/records/'+record_id,headers=auth('reviewer'))
        check('reviewer can inspect immutable assembly payload',detail.status_code==200 and bool(detail.json()['payload']['receipts']))
        check('viewer cannot inspect another actor proposal',client.get('/v1/governed/records/'+record_id,headers=auth('viewer')).status_code==404)
    print(json.dumps(dict(status='PASS_SCOPED',checks=checks,model_transport='MOCKED',parser_child='REAL',database='REAL_OWNED_TMPFS',runtime_python=__import__('sys').version,remaining='Real CPU inference, OCR, production restore, dedicated security and all-card qualification are separate.'),default=str))


if __name__ == "__main__":
    main()
