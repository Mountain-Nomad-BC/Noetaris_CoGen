"""Reversible privacy-only API image repair; never migrate or upgrade feature code."""
from __future__ import annotations
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
import urllib.error
import urllib.request
import uuid
ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'evidence/live-evidence-privacy'
OVERLAY=ROOT/'deploy/local/compose.evidence-privacy.yaml'
COMPOSE=['docker','compose','-f','compose.yaml','-f','deploy/local/compose.cpu.yaml']
PRIVATE=re.compile(r'(?i)(?:[A-Z]:[\\/](?:Users|Documents and Settings)[\\/]|/(?:home|Users)/[^/\s]+/)')

def command(arguments,**kwargs):
    return subprocess.run(arguments,cwd=ROOT,capture_output=True,text=True,check=True,timeout=120,**kwargs)

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

def private_paths(value):
    if isinstance(value,str):return bool(PRIVATE.search(value))
    if isinstance(value,dict):return any(private_paths(item) for item in value.values())
    if isinstance(value,list):return any(private_paths(item) for item in value)
    return False

def summary(data):
    receipts=[]
    for item in data.get('receipts',[]):
        name=item.get('name')
        if not isinstance(name,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_. -]{0,99}',name):continue
        receipt={'name':name,'status':item.get('status') if item.get('status') in {'PASS','FAIL','BLOCKED','PENDING','SKIPPED'} else 'UNVERIFIED','qualification':'historical reported result; current full upgrade qualification is separate'}
        if type(item.get('exit_code')) is int:receipt['exit_code']=item['exit_code']
        checksum=item.get('output_sha256')
        if isinstance(checksum,str) and re.fullmatch('[a-f0-9]{64}',checksum):receipt['output_sha256']=checksum
        captured=item.get('captured_at')
        try:
            when=datetime.datetime.fromisoformat(captured)
            if when.tzinfo is not None:receipt['captured_at']=when.astimezone(datetime.timezone.utc).isoformat()
        except (TypeError,ValueError):pass
        receipts.append(receipt)
    result={'status':'PARTIAL','captured_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'privacy-repaired deployed baseline; full feature upgrade remains separately gated','receipts':receipts[:100],'public_production_clearance':False,'central_integration_enabled':False,'generated_execution_enabled':False,'future_hardware_integrations':'deferred','paths_or_commands_included':False}
    if private_paths(result):raise ValueError('Allowlisted summary contains a private path')
    return result

def patch_old_api(source):
    mount=re.search(r"(?m)^app\.mount\((['\"])/assets\1,\s*StaticFiles\(",source)
    if mount is None or 'class PrivacyPublicAssets' in source:raise ValueError('Expected old static mount seam unavailable')
    if 'JSONResponse' not in source:raise ValueError('Expected old response import unavailable')
    newline='\r\n' if '\r\n' in source else '\n'
    addition=newline.join([
        'class PrivacyPublicAssets(StaticFiles):',
        '    """Reviewed public asset names only; path is normalized by StaticFiles."""',
        '    async def get_response(self,path,scope):',
        "        if path not in {'index.html','index.css','app.js','pdfjs/pdf.mjs','pdfjs/pdf.worker.mjs','pdfjs/LICENSE','pdfjs/provenance.json'}:",
        "            return JSONResponse({'detail':'Not found'},status_code=404,headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','X-Frame-Options':'DENY'})",
        '        return await super().get_response(path,scope)',
        '',
    ])
    result=source[:mount.start()]+addition+source[mount.start():]
    offset=mount.start()+len(addition)
    remainder=result[offset:]
    remainder=remainder.replace('StaticFiles(','PrivacyPublicAssets(',1)
    result=result[:offset]+remainder
    if result.replace(addition,'',1).replace('PrivacyPublicAssets(','StaticFiles(',1)!=source:raise ValueError('Privacy delta altered unrelated old source')
    compile(result,'privacy-patched-old-api.py','exec')
    return result

def inspect_container(identifier):return json.loads(command(['docker','inspect',identifier]).stdout)[0]

def current_api():
    ids=command(COMPOSE+['ps','-q','api']).stdout.split()
    if len(ids)!=1:raise ValueError('Exactly one current API container required')
    return inspect_container(ids[0])

def secret(role):
    filename={'operator':'api_token.txt','reviewer':'reviewer_token.txt','admin':'admin_token.txt','viewer':'viewer_token.txt'}[role]
    path=ROOT/'secrets'/filename
    if path.is_symlink() or path.stat().st_size>4096:raise ValueError('Unexpected role credential source')
    token=path.read_text().strip()
    if not token.isascii() or not 32<=len(token)<=1024:raise ValueError('Invalid role credential configuration')
    return token

def request(base,path,role=None,method='GET'):
    headers={'Authorization':'Bearer '+secret(role)} if role else {}
    request=urllib.request.Request(base+path,headers=headers,method=method)
    try:
        with urllib.request.urlopen(request,timeout=10) as response:
            data=response.read(2*1024*1024+1)
            if len(data)>2*1024*1024:raise ValueError('Read-only API response exceeds probe budget')
            return response.status,data
    except urllib.error.HTTPError as error:return error.code,error.read(16384)

def snapshot(base):
    status,_=request(base,'/healthz')
    if status!=200:raise ValueError('API health precondition failed')
    if request(base,'/readyz')[0]!=200:raise ValueError('Database readiness precondition failed')
    identities={}
    for role in ['operator','viewer','reviewer','admin']:
        status,data=request(base,'/v1/capabilities',role)
        if status!=200:raise ValueError('Role authentication precondition failed')
        identities[role]=digest(json.loads(data).get('identity'))
    if request(base,'/v1/documents')[0]!=401:raise ValueError('Unauthenticated source access did not fail closed')
    status,data=request(base,'/v1/documents','viewer')
    if status!=200:raise ValueError('Read-only document inspection failed')
    docs=json.loads(data)
    status,data=request(base,'/v1/audit','reviewer')
    if status!=200:raise ValueError('Read-only audit inspection failed')
    audit=json.loads(data)
    if audit.get('valid') is not True:raise ValueError('Existing audit chain is not valid')
    status,data=request(base,'/v1/admin/security','admin')
    if status!=200:raise ValueError('Local policy inspection failed')
    policy=json.loads(data)
    if policy.get('central_integration_enabled') is not False:raise ValueError('Central activation not admitted')
    return {'health':200,'readiness':200,'role_identity_hashes':identities,'document_count':len(docs.get('items',[])),'document_identity_sha256':digest(docs),'audit_count':audit['count'],'audit_head_sha256':audit['head_sha256'],'policy_identity_sha256':digest(policy),'unauthenticated_documents_status':401}

def env_map(values):return dict(value.partition('=')[::2] for value in values)

def runtime_policy(data):
    host=data['HostConfig']
    keys=['Memory','NanoCpus','PidsLimit','ReadonlyRootfs','Privileged','CapAdd','CapDrop','SecurityOpt','PortBindings','Tmpfs','LogConfig','Init','RestartPolicy']
    return {'host':{key:host.get(key) for key in keys},'user':data['Config'].get('User'),'command':data['Config'].get('Cmd'),'entrypoint':data['Config'].get('Entrypoint'),'mounts':sorted([(item['Type'],item['Destination'],item.get('Source'),item['RW']) for item in data['Mounts']]),'networks':sorted(data['NetworkSettings']['Networks'])}

def write_overlay(image,context):
    # JSON is an unambiguous YAML subset; no credential values enter this overlay.
    OVERLAY.write_text(json.dumps({'services':{'api':{'image':image,'pull_policy':'never','environment':{'NSAI_MODEL_CONTEXT_TOKENS':context}}}},indent=2))

def wait_healthy():
    deadline=time.monotonic()+90
    while time.monotonic()<deadline:
        data=current_api()
        if data['State'].get('Running') and data['State'].get('Health',{}).get('Status')=='healthy':return data
        time.sleep(1)
    raise ValueError('Privacy candidate did not become healthy within deadline')

def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument('--deploy',action='store_true');args=parser.parse_args(argv)
    OUTPUT.mkdir(parents=True,exist_ok=True)
    run_id=uuid.uuid4().hex[:12];folder=OUTPUT/run_id;folder.mkdir()
    smoke='nsai-evidence-privacy-smoke-'+run_id
    base_tag='nsai-live-evidence-base:'+run_id
    candidate_tag='nsai-live-evidence-privacy:'+run_id
    report={'captured_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'run_id':run_id,'status':'FAIL','scope':'old live API privacy-only image delta; no feature upgrade/schema migration/secret rotation','checks':[],'live_deployment_requested':args.deploy,'full_feature_upgrade':False,'certification':'not granted'}
    previous=current_api();old_image=previous['Image'];old_environment=env_map(previous['Config'].get('Env',[]))
    ports=previous['HostConfig']['PortBindings'].get('8787/tcp') or []
    if len(ports)!=1 or ports[0]['HostIp']!='127.0.0.1':raise ValueError('Expected one loopback-only API port')
    base='http://127.0.0.1:'+ports[0]['HostPort']
    deployed=False;smoke_created=False
    try:
        before=snapshot(base);report['before']=before;report['previous_image_id']=old_image
        other_services={service:command(COMPOSE+['ps','-q',service]).stdout.strip() for service in ['db','parser','llama-cpp']}
        report['non_api_container_ids']=other_services
        command(['docker','cp',previous['Id']+':/app/src/nsai/api.py',str(folder/'api-old.py')])
        original=(folder/'api-old.py').read_bytes();source=original.decode('utf-8');patched=patch_old_api(source)
        (folder/'api.py').write_bytes(patched.encode('utf-8'))
        sanitized=summary(json.loads((ROOT/'assets/verification.json').read_text()))
        (folder/'verification.json').write_text(json.dumps(sanitized,indent=2,ensure_ascii=False))
        report.update(old_api_sha256=hashlib.sha256(original).hexdigest(),patched_api_sha256=hashlib.sha256(patched.encode()).hexdigest(),summary_sha256=hashlib.sha256((folder/'verification.json').read_bytes()).hexdigest())
        command(['docker','image','tag',old_image,base_tag])
        if command(['docker','image','inspect',base_tag,'--format','{{.Id}}']).stdout.strip()!=old_image:raise ValueError('Base-image pin mismatch')
        (folder/'Dockerfile').write_text('FROM '+base_tag+'\nCOPY --chown=10001:10001 api.py /app/src/nsai/api.py\nCOPY --chown=10001:10001 verification.json /app/assets/verification.json\n')
        command(['docker','build','--pull=false','--network=none','-t',candidate_tag,str(folder)])
        candidate=command(['docker','image','inspect',candidate_tag,'--format','{{.Id}}']).stdout.strip();report['candidate_image_id']=candidate
        command(['docker','run','-d','--name',smoke,'--label','nsai.owner=implementation','--label','nsai.privacy=owned-smoke','--network','none','--user','10001:10001','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges:true','--cpus','0.5','--memory','256m','--pids-limit','32','--tmpfs','/tmp:rw,nosuid,nodev,noexec,size=32m,mode=1777',candidate]);smoke_created=True
        probe="""import json,time,urllib.request,urllib.error,pathlib,re
deadline=time.monotonic()+45
while True:
 try:urllib.request.urlopen('http://127.0.0.1:8787/healthz',timeout=1);break
 except Exception:
  if time.monotonic()>deadline:raise RuntimeError('Owned candidate startup deadline exceeded')
  time.sleep(.2)
checks=[]
for method,path in [(method,path) for method in ['GET','HEAD'] for path in ['/assets/verification.json','/assets/%2e/verification.json','/assets/x/%2e%2e/verification.json','/assets//verification.json','/assets/%76erification.json','/assets/VERIFICATION.JSON','/assets/verification.json::$DATA','/assets/app.js::$DATA','/assets/app.js:verification.json']]:
 try:r=urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8787'+path,method=method),timeout=3);status=r.status
 except urllib.error.HTTPError as error:status=error.code
 assert status==404
 checks.append({'method':method,'path_class':'static receipt or normalized alias','status':status})
assert urllib.request.urlopen('http://127.0.0.1:8787/assets/app.js',timeout=3).status==200
data=json.loads(pathlib.Path('/app/assets/verification.json').read_text())
assert data['status']=='PARTIAL' and data['paths_or_commands_included'] is False
assert not re.search(r'[A-Z]:[\\\\/](?:Users|Documents and Settings)[\\\\/]',json.dumps(data),re.I)
print(json.dumps({'status':'PASS','checks':checks,'summary_paths_or_commands':False,'network':'none'}))"""
        proof=json.loads(command(['docker','exec',smoke,'python','-c',probe]).stdout);report['candidate_proof']=proof
        if not args.deploy:
            report['status']='CANDIDATE_VALIDATED';report['deployed']=False;return 0
        if command(['docker','image','inspect',old_image,'--format','{{.Id}}']).stdout.strip()!=old_image:raise ValueError('Original rollback image unavailable')
        report['rollback_prepared']={'exact_original_image_retained':True,'old_api_source_snapshot_saved':True,'database_restore_needed':False,'reason':'API image/configuration-only delta; no database mutation admitted'}
        write_overlay(candidate,'4096')
        config=json.loads(command(COMPOSE+['-f',str(OVERLAY),'config','--format','json']).stdout)
        effective=config['services']['api']['environment']
        for key,value in effective.items():
            if key!='NSAI_MODEL_CONTEXT_TOKENS' and old_environment.get(key)!=str(value):raise ValueError('Unrelated API environment would change; deployment rejected')
        if current_api()['Image']!=old_image or snapshot(base)!=before:raise ValueError('Live baseline changed before admission')
        # Mark uncertain application before command: any partial recreate must roll back.
        deployed=True
        command(COMPOSE+['-f',str(OVERLAY),'up','-d','--no-deps','--no-build','--pull','never','api'])
        after_container=wait_healthy()
        if after_container['Image']!=candidate:raise ValueError('Deployed candidate image mismatch')
        if runtime_policy(after_container)!=runtime_policy(previous):raise ValueError('Shared runtime limits/mounts/networks changed unexpectedly')
        after_environment=env_map(after_container['Config'].get('Env',[]))
        if {key:value for key,value in after_environment.items() if key!='NSAI_MODEL_CONTEXT_TOKENS'}!={key:value for key,value in old_environment.items() if key!='NSAI_MODEL_CONTEXT_TOKENS'} or after_environment.get('NSAI_MODEL_CONTEXT_TOKENS')!='4096':raise ValueError('Unexpected deployed environment change')
        if any(command(COMPOSE+['ps','-q',service]).stdout.strip()!=identifier for service,identifier in other_services.items()):raise ValueError('Non-API service unexpectedly recreated')
        after=snapshot(base);report['after']=after
        if before!=after:raise ValueError('Read-only identity/document/audit/policy preservation check failed')
        for method in ['GET','HEAD']:
            for path in ['/assets/verification.json','/assets/%2e/verification.json','/assets/x/%2e%2e/verification.json','/assets//verification.json','/assets/%76erification.json','/assets/VERIFICATION.JSON','/assets/verification.json::$DATA','/assets/app.js::$DATA','/assets/app.js:verification.json']:
                if request(base,path,method=method)[0]!=404:raise ValueError('Static privacy denial failed after deployment')
        status,payload=request(base,'/v1/submission/evidence','viewer')
        if status!=200 or private_paths(json.loads(payload)):raise ValueError('Authenticated evidence summary failed privacy check')
        report.update(status='PASS',deployed=True,preserved_corpus_and_audit=True,authenticated_summary_status=200,static_get_head_status=404,context_admission_cap=4096,rollback_needed=False)
        return 0
    except BaseException as error:
        report['error_type']=type(error).__name__;report['deployed']=False
        if deployed:
            try:
                write_overlay(old_image,old_environment.get('NSAI_MODEL_CONTEXT_TOKENS'))
                command(COMPOSE+['-f',str(OVERLAY),'up','-d','--no-deps','--no-build','--pull','never','api'])
                restored=wait_healthy();report['rollback_image_matches']=restored['Image']==old_image;report['rollback_snapshot']=snapshot(base)
                report['rollback_verified']=report['rollback_image_matches'] and report['rollback_snapshot']==report['before']
            except BaseException:report['rollback_verified']=False;report['manual_recovery_required']=True
        return 1
    finally:
        if smoke_created:
            details=inspect_container(smoke)
            if (details['Config'].get('Labels') or {}).get('nsai.privacy')!='owned-smoke':raise ValueError('Owned smoke cleanup label mismatch')
            command(['docker','rm','-f',smoke])
            report['owned_smoke_removed']=True
        report['runner_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        (folder/'result.json').write_text(json.dumps(report,indent=2))
        (OUTPUT/'latest.json').write_text(json.dumps(report,indent=2))
        print(json.dumps(report,indent=2))

if __name__=='__main__':raise SystemExit(main())
