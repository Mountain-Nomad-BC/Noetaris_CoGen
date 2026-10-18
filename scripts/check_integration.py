"""Real HTTP checks against the fixed, isolated synthetic integration project."""
import json
from pathlib import Path
import time
import urllib.error
import urllib.request
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
STATE=ROOT/'state/integration'
OUTPUT=ROOT/'evidence/integration-deployment'


def main():
    identity=json.loads((STATE/'identity.json').read_text())
    assert identity['project']=='noetaris-integration' and identity['url']=='http://127.0.0.1:8790'
    OUTPUT.mkdir(parents=True,exist_ok=True)
    checks=[]
    def request(path,role=None,body=None,method=None):
        headers={'Content-Type':'application/json'}
        if role:headers['Authorization']='Bearer '+(STATE/'secrets'/f'{role}.txt').read_text().strip()
        req=urllib.request.Request(identity['url']+path,headers=headers,
            data=json.dumps(body).encode() if body is not None else None,method=method)
        try:response=urllib.request.urlopen(req,timeout=150)
        except urllib.error.HTTPError as error:response=error
        raw=response.read(32*1024*1024+1)
        assert len(raw)<=32*1024*1024
        try:value=json.loads(raw)
        except ValueError:value=None
        return response.status,value,raw
    def check(name,condition,details=None,*,fatal=True):
        checks.append(dict(name=name,passed=bool(condition),details=details))
        print(name+': '+('PASS' if condition else 'FAIL'),flush=True)
        if not condition and fatal:raise AssertionError(name)
    report=dict(scope='Synthetic isolated real HTTP/DB/parser/CPU checks; not release acceptance',identity=identity,checks=checks)
    try:
        check('Database schema readiness via UI proxy',request('/readyz')[0]==200)
        check('Anonymous source access denied',request('/v1/documents')[0]==401)
        check('Private verification artifact denied',request('/pdf-runtime/verification.json')[0]==404)
        check('Viewer upload denied',request('/v1/documents','viewer',dict(title='denied',text='denied'))[0]==403)
        check('All roles denied generated execution',all(request('/v1/execute',r,{},'POST')[0]==403 for r in ['operator','viewer','reviewer','admin']))
        check('Public demo upload restrictions require acknowledgment',request('/v1/documents','operator',dict(title='unacknowledged',text='Synthetic rejected input'))[0]==428)
        tag=uuid4().hex[:8]
        # Each run uses a new supported extractor subject and version.
        subject='Pump-'+tag
        source=dict(title='Synthetic integration '+tag,text=subject+' operating limit is 85 C.',version=tag,upload_ack='public-demo-2026-10-17')
        status,created,_=request('/v1/documents','operator',source)
        check('Real source ingestion',status==200,created)
        document=created['document_id']
        for _ in range(120):
            _,index,_=request('/v1/sources/'+document+'/index','operator')
            if index.get('ready') is True:break
            time.sleep(.5)
        check('Durable source indexing publishes generation',index.get('ready') is True,index)
        status,scoped,_=request('/v1/chat','operator',dict(question=subject,document_ids=[document],request_id=uuid4().hex))
        check('Scoped retrieval with exact source citation',status==200 and not scoped['conflicts'] and bool(scoped['citations']) and all(c['document_id']==document for c in scoped['citations']),dict(status=status,result=scoped))
        check('Original bytes roundtrip',request('/v1/sources/'+document+'/original','viewer')[2]==source['text'].encode())
        check('Stale revision rejected',request('/v1/chat','operator',dict(question=subject,document_ids=[document],revision='stale'))[0]==409)
        status,items,_=request('/v1/claims','reviewer')
        selected=next(c for c in items['items'] if c['document_id']==document)
        status,review,_=request('/v1/review/'+selected['id'],'reviewer',dict(decision='accept',expected_revision=selected['revision'],rationale='Synthetic integration fixture review only'))
        check('Separate reviewer persists claim decision',status==200,review)
        started=time.monotonic()
        status,reason,_=request('/v1/reason','operator',dict(question='What is '+subject+' operating limit?',document_ids=[document],request_id=uuid4().hex))
        check('Real CPU inference through complete HTTP path',status==200 and bool(reason.get('run_id')) and reason.get('token_admission',{}).get('admitted') is True and reason.get('answer_verified') is False,dict(status=status,result=reason,wall_seconds=round(time.monotonic()-started,3)))
        # Retain model quality failures while still exercising later conflict,
        # quarantine and audit cases. The final run remains FAIL if any fail.
        check('Grounded synthetic numeric answer',reason.get('mode')=='model_unverified' and '85' in reason.get('answer',''),dict(mode=reason.get('mode'),answer=reason.get('answer')),fatal=False)
        other=dict(title='Synthetic conflicting '+tag,text=subject+' operating limit is 75 C.',version=tag+'-conflict')
        other['upload_ack']='public-demo-2026-10-17'
        other_status,other_created,_=request('/v1/documents','operator',other)
        check('Conflicting source persisted',other_status==200)
        for _ in range(120):
            _,index,_=request('/v1/sources/'+other_created['document_id']+'/index','operator')
            if index.get('ready') is True:break
            time.sleep(.5)
        check('Conflicting source index ready',index.get('ready') is True,index)
        status,disputed,_=request('/v1/reason','operator',dict(question=subject,document_ids=[document,other_created['document_id']],request_id=uuid4().hex))
        check('Real persisted conflict withholds inference',status==200 and disputed.get('mode')=='evidence-extract' and bool(disputed.get('conflicts')) and 'run_id' not in disputed and disputed.get('answer_verified') is False)
        check('Real reviewed memory quarantined',
              all(c['id']!=selected['id'] for c in disputed['memory']['canon']) and
              any(c['claim_id']==selected['id'] for c in disputed['memory']['quarantined']))
        check('Cross-role session denied',request('/v1/memory/'+scoped['session_id'],'admin')[0]==403)
        status,audit,_=request('/v1/audit','reviewer')
        check('Durable audit chain validates',status==200 and audit.get('valid') is True)
        if not all(c['passed'] for c in checks):
            raise AssertionError('Integration checks completed with retained failures')
        report['status']='PASS'
    except Exception as error:
        report.update(status='FAIL',failure_type=type(error).__name__,failure=str(error))
        raise
    finally:
        path=OUTPUT/('http-'+uuid4().hex+'.json')
        path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        print('Evidence: '+str(path),flush=True)


if __name__=='__main__':main()
