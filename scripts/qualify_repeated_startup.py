"""One hundred bounded, owned API/parser cold starts without model access."""
import importlib.util
import json
from pathlib import Path
import secrets
import tempfile
import time
from qualify_local_stack import Stack, ROOT, command

COUNT = 100
DEADLINE = 30
API = 'sha256:7194ff27016ad9fdc1929e2c7f49bf013c1f32fb1cfa8e181bca5333554b2490'
DB = 'sha256:e8d60b4d26e679424148c662d01229c05d0d661745d846e7911af78b88bd9f6d'
PROBE = r'''import urllib.request,urllib.error,json,time
def get(url,method='GET',body=None):
 r=urllib.request.Request(url,method=method,data=body,headers={'Content-Type':'application/json'} if body else {})
 try:r=urllib.request.urlopen(r,timeout=2)
 except urllib.error.HTTPError as e:r=e
 return [r.status,dict(r.headers),r.read(65537).decode()]
start=time.monotonic()
while time.monotonic()-start<20:
 try:
  ready=get('http://127.0.0.1:8787/readyz');parser=get('http://parser:8788/healthz')
  if ready[0]==200 and parser[0]==200:break
 except (OSError,urllib.error.URLError):pass
 time.sleep(.1)
else:raise RuntimeError('startup readiness deadline')
print(json.dumps({'ready':ready,'parser':parser,'anonymous':get('http://127.0.0.1:8787/v1/documents')[0],'parser_denial':get('http://parser:8788/parse','POST',b'{"filename":"synthetic.txt","data":"c3ludGhldGlj"}')[0]}))'''

def main():
    stack = Stack(ROOT/'evidence/implementation/repeated-startup', DB, 'nsai-ocr-hardened-candidate:local')
    stack.api_image=API; stack.receipt['images']['api']=API
    stack.receipt.update(predeclared_iterations=COUNT,deadline_seconds=DEADLINE,aggregate_cpu_cap=2,aggregate_memory_mib=1920,no_model_access=True,iterations=[])
    stack.save()
    spec=importlib.util.spec_from_file_location('startup_migrate',ROOT/'scripts/migrate.py')
    migrate=importlib.util.module_from_spec(spec);spec.loader.exec_module(migrate)
    try:
        with tempfile.TemporaryDirectory(prefix=stack.prefix) as folder:
            directory=Path(folder);keys={role:secrets.token_hex(32) for role in ('operator','reviewer','admin','viewer','parser','db')}
            for role,value in keys.items():(directory/(role+'.txt')).write_text(value)
            dbnet=stack.network('db');parsernet=stack.network('parser')
            db=stack.db('db',dbnet,secrets.token_hex(32));command(['docker','update','--cpus','.25',db])
            stack.sql(db,migrate.migration_sql(ROOT)+'COMMIT;')
            stack.sql(db,'BEGIN;'+migrate.role_sql(keys['db'],include_commit=False)+'COMMIT;')
            before=stack.fingerprint(db);stack.receipt['database_before']=before;stack.save()
            env={'NSAI_DB_HOST':'db','NSAI_DB_NAME':'nsai','NSAI_DB_USER':'nsai_app','NSAI_DB_PASSWORD_FILE':'/qualification-secrets/db.txt','NSAI_CENTRAL_SECURITY_ENABLED':'false','NSAI_PARSER_URL':'http://parser:8788','NSAI_PARSER_TOKEN_FILE':'/qualification-secrets/parser.txt'}
            for role,name in [('operator','API'),('reviewer','REVIEWER'),('admin','ADMIN'),('viewer','VIEWER')]:env['NSAI_'+name+'_TOKEN_FILE']='/qualification-secrets/'+role+'.txt'
            mount=['--mount',f'type=bind,source={directory},target=/qualification-secrets,readonly']
            for i in range(COUNT):
                start=time.monotonic();entry={'iteration':i+1,'status':'RUNNING'};stack.receipt['iterations'].append(entry);stack.save();owned=[]
                try:
                    parser=stack.run('parser-'+str(i+1),API,mount+['--cpus','.75','--env','NSAI_PARSER_TOKEN_FILE=/qualification-secrets/parser.txt'],['uvicorn','nsai.parser:app','--host','0.0.0.0','--port','8788','--no-access-log'],network=parsernet,alias='parser',memory='384m',pids='32');owned.append(parser)
                    options=mount[:]
                    for key,value in env.items():options+=['--env',key+'='+value]
                    api=stack.run('api-'+str(i+1),API,options,['uvicorn','nsai.api:app','--host','0.0.0.0','--port','8787','--no-access-log'],network=dbnet,memory='768m',pids='64');owned.append(api)
                    command(['docker','network','connect',parsernet,api])
                    remaining=DEADLINE-(time.monotonic()-start)
                    if remaining<=0:raise TimeoutError('cold setup deadline')
                    result=json.loads(command(['docker','exec',api,'python','-c',PROBE],timeout=remaining))
                    entry['probe']=result
                    assert result['anonymous']==401 and result['parser_denial']==401
                    headers={k.lower():v for k,v in result['ready'][1].items()}
                    assert headers['x-content-type-options']=='nosniff' and headers['x-frame-options']=='DENY' and headers['cache-control']=='no-store' and 'frame-ancestors' in headers['content-security-policy']
                    policies=[]
                    for item in json.loads(command(['docker','inspect',api,parser])):
                        h=item['HostConfig'];assert h['ReadonlyRootfs'] and 'ALL' in h['CapDrop'] and 'no-new-privileges:true' in h['SecurityOpt'] and not h['PortBindings'] and item['Config']['User']=='10001:10001' and set(item['NetworkSettings']['Networks'])<=set((dbnet,parsernet))
                        policies.append({'memory_bytes':h['Memory'],'nano_cpus':h['NanoCpus'],'pids_limit':h['PidsLimit'],'readonly':True,'no_ports':True,'private_networks_only':True})
                    entry.update(status='PASS',startup_seconds=time.monotonic()-start,probe=result,resource_policies=policies)
                except Exception as error:
                    entry.update(status='FAIL',elapsed_seconds=time.monotonic()-start,failure_type=type(error).__name__);stack.save();raise
                finally:
                    for name in reversed(owned):
                        info=json.loads(command(['docker','inspect',name]))[0];assert info['Config']['Labels']['nsai.owner']==stack.tag
                        command(['docker','rm','-f',name]);stack.containers.remove(name)
                    stack.save()
                if (i+1)%25==0:print(json.dumps({'completed':i+1,'predeclared':COUNT}),flush=True)
            after=stack.fingerprint(db);stack.receipt['database_after']=after;assert before==after
            latencies=sorted(entry['startup_seconds'] for entry in stack.receipt['iterations'])
            stack.receipt.update(status='PASS',database_unchanged=True,samples=COUNT,p50_seconds=latencies[49],p95_seconds=latencies[94],max_seconds=max(latencies))
    except Exception as error:
        stack.receipt.update(status='FAIL',failure_type=type(error).__name__);raise
    finally:
        stack.cleanup();print(json.dumps({'status':stack.receipt['status'],'samples':len(stack.receipt['iterations']),'cleanup':stack.receipt.get('cleanup_complete')}),flush=True)

if __name__=='__main__':main()
