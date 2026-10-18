"""Exercise the real pinned CPU encoder in an owned network-none container.

No live services, credentials, user documents or host ports are used. PASS_SCOPED
means this service smoke/isolation contract, never release or retrieval acceptance.
"""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import secrets
import subprocess
import time
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]


def main():
    started=time.monotonic()
    owner=uuid4().hex;name='nsai-encoder-qualification-'+owner[:12]
    folder=ROOT/'evidence/encoder-service'/owner;folder.mkdir(parents=True)
    token=secrets.token_hex(32)
    def command(args,*,data=None,timeout=120,ok=True):
        result=subprocess.run(['docker',*args],input=data,capture_output=True,text=True,timeout=timeout)
        if ok and result.returncode:
            raise RuntimeError('Owned encoder command failed: '+result.stderr.replace(token,'[owned credential]')[-1200:])
        return result
    image=command(['image','inspect','nsai-cpu-encoder:qualification','--format','{{.Id}}']).stdout.strip()
    model=ROOT/'state/models/all-MiniLM-L6-v2'
    report=dict(status='FAIL',scope='Real CPU encoder service smoke and isolation, not release acceptance',
        run_id=owner,image_id=image,recorded_at=datetime.now(timezone.utc).isoformat(),cleanup=False,
        command=['python','scripts/qualify_encoder_service.py'],
        producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        model_manifest_sha256=hashlib.sha256((model/'manifest.json').read_bytes()).hexdigest())
    wrapper="from pathlib import Path;Path('/tmp/encoder-token').write_text("+repr(token)+");import uvicorn;uvicorn.run('nsai.encoder_service:app',host='127.0.0.1',port=8092,access_log=False,log_level='warning')"
    try:
        command(['run','-d','--name',name,'--label','nsai.owner='+owner,'--network','none',
            '--read-only','--cap-drop','ALL','--security-opt','no-new-privileges:true','--user','10001:10001',
            '--pids-limit','64','--memory','768m','--cpus','2',
            '--tmpfs','/tmp:rw,nosuid,nodev,noexec,size=32m,mode=1777',
            '--mount','type=bind,source='+str(model)+',target=/models,readonly',
            '-e','NSAI_ENCODER_MODEL_DIR=/models','-e','NSAI_ENCODER_TOKEN_FILE=/tmp/encoder-token',
            '--entrypoint','python',image,'-c',wrapper])
        probe="import urllib.request;urllib.request.urlopen('http://127.0.0.1:8092/healthz',timeout=3)"
        for _ in range(60):
            if command(['exec',name,'python','-c',probe],ok=False,timeout=10).returncode==0:break
            time.sleep(.25)
        else:raise RuntimeError('Owned encoder readiness deadline exceeded')
        program=r'''
import json,math,os,signal,time,urllib.request,urllib.error
checks=[]
def check(name,value):
 if not value:raise AssertionError(name)
 checks.append(name)
def request(path,payload=None,authenticated=True):
 headers={'Content-Type':'application/json'}
 if authenticated:headers['Authorization']='Bearer '+TOKEN
 req=urllib.request.Request('http://127.0.0.1:8092'+path,data=json.dumps(payload).encode() if payload is not None else None,headers=headers)
 try:
  with urllib.request.urlopen(req,timeout=100) as response:return response.status,json.load(response)
 except urllib.error.HTTPError as error:return error.code,json.loads(error.read())
check('unauthenticated encoding denied',request('/encode',{'texts':['canary']},False)[0]==401)
identity=request('/identity')[1]['model_identity']
check('exact pinned model identity',identity['sha256']=='6fd5d72fe4589f189f8ebc006442dbb529bb7ce38f8082112682524616046452')
texts=['The electric motor can run at a maximum temperature of 85 degrees Celsius.','What is the highest allowed operating temperature of the motor?','The sea otter is eating shellfish near the ocean.']
encoded=request('/encode',{'texts':texts})[1]
check('complete finite normalized 384-dimensional vectors',len(encoded['vectors'])==3 and all(len(v)==384 and all(math.isfinite(x) for x in v) and abs(sum(x*x for x in v)-1)<1e-5 for v in encoded['vectors']))
cos=lambda a,b:sum(x*y for x,y in zip(a,b))
related=cos(encoded['vectors'][0],encoded['vectors'][1]);unrelated=cos(encoded['vectors'][0],encoded['vectors'][2])
check('declared paraphrase smoke ranks above unrelated text',related>unrelated)
long=request('/encode',{'texts':['safety '*3000]})[1]
coverage=long['coverage'][0]
check('long passage windows cover all tokenizer input',coverage['complete'] and coverage['covered_tokens']==coverage['input_tokens'] and coverage['input_tokens']>256 and coverage['windows']>1)
check('oversized batch denied',request('/encode',{'texts':['x']*9})[0]==422)
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
barrier=Barrier(3)
def concurrent_query(_):
 barrier.wait(timeout=10)
 return request('/encode',{'texts':['safety '*3000]})[0]
with ThreadPoolExecutor(max_workers=3) as executor:concurrent_statuses=list(executor.map(concurrent_query,range(3)))
check('two workers and one query queue without busy rejection',concurrent_statuses==[200,200,200])
children=[]
for entry in os.listdir('/proc'):
 if not entry.isdigit():continue
 try:
  raw=open('/proc/'+entry+'/cmdline','rb').read()
  if b'nsai.semantic_child' in raw:children.append(int(entry))
 except (FileNotFoundError,PermissionError):pass
check('one bounded reusable encoder child',len(children)==1)
environment=open('/proc/'+str(children[0])+'/environ','rb').read().split(bytes([0]))
keys=[item.split(b'=',1)[0].decode() for item in environment if item]
check('child receives no database or API or service credential environment','NSAI_ENCODER_MODEL_DIR' in keys and not any(key.startswith(('NSAI_DB_','NSAI_API_','NSAI_ENCODER_TOKEN')) for key in keys))
os.kill(children[0],signal.SIGKILL);time.sleep(.1)
check('killed encoder child recovers on next request',request('/encode',{'texts':['A fresh bounded request after child death.']})[0]==200)
print(json.dumps(dict(status='PASS_SCOPED',checks=checks,model_identity=identity,paraphrase_cosine=related,unrelated_cosine=unrelated,long_coverage=coverage)))
'''
        result=command(['exec','-i',name,'python','-'],data='TOKEN='+repr(token)+'\n'+program,timeout=240)
        report['execution']=json.loads(result.stdout)
        report['execution_exit_code']=result.returncode
        report['execution_stdout_sha256']=hashlib.sha256(result.stdout.encode()).hexdigest()
        inspected=json.loads(command(['inspect',name]).stdout)[0]
        runtime=inspected['HostConfig']
        report['runtime']=dict(network=runtime['NetworkMode'],read_only=runtime['ReadonlyRootfs'],
            capabilities_dropped=runtime['CapDrop'],memory_bytes=runtime['Memory'],pid_limit=runtime['PidsLimit'],
            cpu_nanoseconds=runtime['NanoCpus'],user=inspected['Config']['User'],
            mounts=[dict(target=m['Destination'],read_only=not m['RW']) for m in inspected['Mounts']])
        assert report['runtime']['network']=='none' and report['runtime']['read_only']
        assert report['runtime']['mounts']==[dict(target='/models',read_only=True)]
        report['status']='PASS_SCOPED'
    except Exception as error:
        report['failure']=dict(type=type(error).__name__,message=str(error).replace(token,'[owned credential]')[:1800])
    finally:
        existing=command(['inspect',name],ok=False)
        if existing.returncode==0:
            info=json.loads(existing.stdout)[0]
            if info['Config'].get('Labels',{}).get('nsai.owner')!=owner:
                raise RuntimeError('Unowned encoder cleanup refused')
            report['cleanup']=command(['rm','--force',name],ok=False).returncode==0
        else:report['cleanup']=True
        if not report['cleanup']:report['status']='FAIL'
        report['elapsed_seconds']=round(time.monotonic()-started,3)
        (folder/'receipt.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=report['status'],run_id=owner,cleanup=report['cleanup'],
                         checks=len(report.get('execution',{}).get('checks',[])))))
    return 0 if report['status']=='PASS_SCOPED' else 1


if __name__=='__main__':raise SystemExit(main())
