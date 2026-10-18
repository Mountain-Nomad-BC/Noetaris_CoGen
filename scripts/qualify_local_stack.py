"""Owned real HTTP/Chromium/parser/OCR/DB/model and restore qualification.

Never connects to the production database or changes existing app containers.
Only one source-supported call uses the existing private CPU model. Every new
container/network carries an exact random ownership label and is removed safely.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import tempfile
import time
import urllib.request
import urllib.error
from uuid import uuid4
from datetime import datetime,timezone
from evidence_contract import admit_receipt

ROOT=Path(__file__).resolve().parents[1]

def command(args,*,input=None,timeout=60):
    run=subprocess.run(args,input=input,capture_output=True,timeout=timeout)
    if run.returncode:raise RuntimeError('Owned command failed: '+args[0]+' '+args[1]+' (diagnostics withheld; inspect owned resource locally)')
    return run.stdout

def image_id(name):return json.loads(command(['docker','image','inspect',name]))[0]['Id']

def source_hashes():
    result={}
    for directory in ('src','assets','database/migrations'):
        for path in (ROOT/directory).rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts:
                result[path.relative_to(ROOT).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
    for name in ('deploy/init.sql','scripts/migrate.py','scripts/qualify_local_stack.py','scripts/evidence_contract.py','compose.yaml','deploy/local/compose.cpu.yaml','Dockerfile','requirements.lock','requirements-build.lock'):
        result[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    return result

def identity_hash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def public_runtime_policy(data,network_types):
    """Allowlisted effective policy only: no environment, mount sources or names."""
    host=data['HostConfig'];configuration=data['Config']
    command_tokens=configuration.get('Cmd') or []
    # Owned command shapes only; arbitrary image defaults are bound by digest,
    # never projected into this sidecar as potentially sensitive text.
    safe_commands={'uvicorn','nsai.api:app','nsai.parser:app','--host','0.0.0.0','--port','8787','8788','--no-access-log','postgres','python','-m','nsai.ocr_service'}
    command_shape=[token if token in safe_commands else '<opaque-argument>' for token in command_tokens]
    return dict(image_digest=data['Image'],user=configuration.get('User',''),command=command_shape,command_sha256=identity_hash(command_tokens),
        readonly=host.get('ReadonlyRootfs',False),privileged=host.get('Privileged',False),
        cap_drop=sorted(host.get('CapDrop') or []),cap_add=sorted(host.get('CapAdd') or []),
        security_opt=sorted(host.get('SecurityOpt') or []),memory=host.get('Memory'),nano_cpus=host.get('NanoCpus'),pids_limit=host.get('PidsLimit'),
        network_types=sorted(network_types),
        mounts=sorted([dict(destination=m['Destination'],readonly=not m.get('RW',False),type=m['Type']) for m in data.get('Mounts',[])],key=lambda m:m['destination']),
        tmpfs=host.get('Tmpfs') or {},logging=host.get('LogConfig') or {},
        published_ports=sorted([dict(container_port=port,loopback=entry.get('HostIp')=='127.0.0.1') for port,entries in (host.get('PortBindings') or {}).items() for entry in entries],key=lambda p:p['container_port']))

def stack_envelope(raw,identity,*,captured_at=None):
    """Verdict from final bytes, never intermediate status or successful exit alone."""
    receipt=json.loads(raw)
    passed=(receipt.get('status')=='PASS' and bool(receipt.get('cases')) and
            all(case.get('pass_') is True for case in receipt['cases']) and
            receipt.get('cleanup_complete') is True and
            bool(receipt.get('sources_before')) and receipt.get('sources_before')==receipt.get('sources_after') and
            receipt.get('identity_capture_complete') is True)
    envelope=dict(identity,scope='runtime',status='PASS' if passed else 'FAIL',exit_code=0 if passed else 1,
                  captured_at=captured_at or datetime.now(timezone.utc).isoformat(),evidence_sha256=hashlib.sha256(raw).hexdigest())
    return dict(receipt=envelope,admission=admit_receipt(envelope,raw,identity),release_approval=False,certification=False)

class Stack:
    def __init__(self,output,db_image,ocr_image):
        self.output=output;self.output.mkdir(parents=True,exist_ok=True)
        self.tag=uuid4().hex[:12];self.prefix='nsai-qual-stack-'+self.tag
        self.run_id=uuid4().hex
        self.containers=[];self.networks=[];self.cases=[];self.receipt=dict(scope=self.prefix,cases=self.cases,status='running',started_at=datetime.now(timezone.utc).isoformat(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
        self.before=source_hashes();self.receipt['sources_before']=self.before
        self.api_image=image_id('nsai-implementation-candidate:local')
        self.ocr_image=image_id(ocr_image)
        self.db_image=image_id(db_image)
        self.receipt['images']=dict(api=self.api_image,ocr=self.ocr_image,db=self.db_image)
    def save(self):
        (self.output/'receipt.json').write_text(json.dumps(self.receipt,indent=2),encoding='utf-8')
    def case(self,name,passed,details=None):
        self.cases.append(dict(name=name,pass_=bool(passed),details=details,captured_at=datetime.now(timezone.utc).isoformat()));self.save()
        if not passed:raise AssertionError(name)
    def network(self,suffix,internal=True):
        name=self.prefix+'-'+suffix
        command(['docker','network','create']+(['--internal'] if internal else [])+['--label','nsai.owner='+self.tag,name]);self.networks.append(name);return name
    def run(self,suffix,image,options,program=None,network=None,alias=None,user='10001:10001',memory='768m',pids='64'):
        name=self.prefix+'-'+suffix
        args=['docker','run','-d','--name',name,'--label','nsai.owner='+self.tag,'--read-only','--cap-drop','ALL','--security-opt','no-new-privileges:true',
            '--cpus','1','--memory',memory,'--pids-limit',pids,'--user',user,'--tmpfs','/tmp:rw,noexec,nosuid,size=128m']
        if network:args+=['--network',network]
        if alias:args+=['--network-alias',alias]
        args+=options+[image]+(program or [])
        command(args);self.containers.append(name);return name
    def sql(self,container,sql):
        return command(['docker','exec','-i',container,'psql','-v','ON_ERROR_STOP=1','-At','-U','nsai','-d','nsai'],input=sql.encode(),timeout=120).decode()
    def db(self,suffix,network,password):
        name=self.run(suffix,self.db_image,['--tmpfs','/var/lib/postgresql/data:rw,nosuid,size=256m,mode=1777','--tmpfs','/var/run/postgresql:rw,nosuid,size=8m,mode=1777',
            '--env','POSTGRES_USER=nsai','--env','POSTGRES_DB=nsai','--env','POSTGRES_PASSWORD='+password,'--env','PGDATA=/var/lib/postgresql/data/pgdata'],network=network,alias=suffix,user='70:70')
        for _ in range(60):
            run=subprocess.run(['docker','exec',name,'pg_isready','-h','127.0.0.1','-U','nsai','-d','nsai'],capture_output=True)
            if run.returncode==0:return name
            time.sleep(.25)
        raise RuntimeError('Owned database readiness deadline exceeded')
    def http(self,path,role=None,method='GET',body=None):
        headers={'Content-Type':'application/json'}
        if role:headers['Authorization']='Bearer '+self.tokens[role]
        request=urllib.request.Request(self.base+path,method=method,headers=headers,data=json.dumps(body).encode() if body is not None else None)
        try:
            response=urllib.request.urlopen(request,timeout=140)
        except urllib.error.HTTPError as error:response=error
        data=response.read(16*1024*1024+1)
        if len(data)>16*1024*1024:raise ValueError('Qualification HTTP response budget exceeded')
        try:result=json.loads(data)
        except ValueError:result=None
        return response.status,result,dict(response.headers),data
    def connect(self,page,role):
        page.fill('#token',self.tokens[role]);page.click('#connect')
        self.receipt['browser_connect_state']=page.evaluate('() => ({ready:document.readyState,disabled:document.getElementById("connect").disabled,hasClickHandler:typeof document.getElementById("connect").onclick,pending:typeof pendingRequests!=="undefined"?pendingRequests.size:null,epoch:typeof authEpoch!=="undefined"?authEpoch:null,tokenLength:typeof token!=="undefined"?token.length:null,inputTokenLength:document.getElementById("token").value.length})');self.save()
        try:page.wait_for_function('(role) => document.getElementById("identity").textContent.includes(role)',arg=role,timeout=30000)
        except Exception:
            self.receipt['browser_health_probe']=page.evaluate('''async () => {const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),5000);try {const response=await fetch('/healthz',{signal:controller.signal});return {status:response.status,body:await response.json()};}catch(e){return {error:e.name};}finally{clearTimeout(timer);}}''')
            self.receipt['browser_failure_context']=dict(identity=page.inner_text('#identity'),notice=page.inner_text('#notice'),page_errors=self.receipt.get('browser_page_errors',[]),state=page.evaluate('() => ({disabled:document.getElementById("connect").disabled,hasClickHandler:typeof document.getElementById("connect").onclick,pending:pendingRequests.size,epoch:authEpoch,tokenLength:token.length,inputTokenLength:document.getElementById("token").value.length,identityPresent:identity!==null})'));self.save()
            raise
        page.wait_for_function('() => !document.getElementById("connect").disabled',timeout=30000)
    def browser(self,ocr_pdf):
        from playwright.sync_api import sync_playwright
        with sync_playwright() as playwright:
            browser=playwright.chromium.launch(headless=True)
            context=browser.new_context()
            context.grant_permissions(['local-network-access'],origin=self.base)
            self.receipt['browser_permission']='Local-network-access granted only to owned loopback origin for real Chromium qualification; no browser security flag disabled'
            page=context.new_page();errors=[]
            self.receipt['browser_page_errors']=errors
            self.receipt['browser_console_errors']=[]
            self.receipt['browser_static_requests']=[]
            self.receipt['browser_request_metadata']=[]
            self.receipt['browser_request_failures']=[]
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.on('console',lambda message:self.receipt['browser_console_errors'].append(message.text) if message.type=='error' else None)
            page.on('response',lambda response:self.receipt['browser_static_requests'].append(dict(url=response.url,status=response.status,content_type=response.headers.get('content-type'))) if '/assets/' in response.url else None)
            page.on('request',lambda request:self.receipt['browser_request_metadata'].append(dict(url=request.url,method=request.method,resource_type=request.resource_type,authorization_matches_owned_operator=request.headers.get('authorization')=='Bearer '+self.tokens['operator'] if '/v1/capabilities' in request.url else None)))
            page.on('requestfailed',lambda request:self.receipt['browser_request_failures'].append(dict(url=request.url,failure=request.failure)))
            page.goto(self.base,wait_until='networkidle')
            self.receipt['browser_boot']=page.evaluate('() => ({requestType:typeof request,viewType:typeof view,guardedType:typeof guarded,scripts:[...document.scripts].map(s=>s.src),ready:document.readyState,hasClickHandler:typeof document.getElementById("connect").onclick})');self.save()
            self.connect(page,'operator')
            page.click('[data-view="sources"]');page.set_input_files('#file',str(ocr_pdf));page.fill('#file-version','ocr-test-1')
            with page.expect_response(lambda response:'/v1/files' in response.url and response.request.method=='POST',timeout=140000) as response:
                page.click('#upload-file')
            actual=response.value.json();self.case('Chromium real raster PDF upload/OCR',response.value.status==200 and actual.get('created'),dict(document_id=actual.get('document_id')))
            self.ocr_doc=actual['document_id']
            page.wait_for_function('() => !document.getElementById("upload-file").disabled',timeout=30000)
            card=page.locator('#documents .card').filter(has_text=ocr_pdf.name)
            card.get_by_role('button',name='Inspect source & manifest').click()
            page.wait_for_function('() => !document.getElementById("open-pdf").disabled',timeout=30000)
            page.click('[data-view="chat"]');page.click('#open-pdf')
            page.wait_for_function('() => document.getElementById("pdf-canvas").width>0 && document.getElementById("pdf-status").textContent.includes("original SHA256")',timeout=40000)
            pixels=page.evaluate('''() => {const c=document.getElementById('pdf-canvas'),p=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let marked=0;for(let i=0;i<p.length;i+=4)if(p[i]<240||p[i+1]<240||p[i+2]<240)marked++;return {width:c.width,height:c.height,marked};}''')
            self.case('Chromium exact private PDF worker/canvas',pixels['marked']>100,pixels)
            page.fill('#question','What is the maximum temperature?')
            with page.expect_response(lambda response:'/v1/chat' in response.url and response.request.method=='POST') as response:
                page.click('#send')
            response=response.value;question=response.request.post_data_json;answer=response.json()
            self.case('Chromium exact document/revision/page question',response.status==200 and question.get('document_ids')==[self.ocr_doc] and question.get('revision')=='ocr-test-1' and question.get('pages')==[1]
                and bool(answer.get('citations')) and all(c['document_id']==self.ocr_doc for c in answer['citations']),dict(request_scope={k:question.get(k) for k in ('document_ids','revision','pages')},mode=answer.get('mode')))
            page.click('#assemble-source');page.wait_for_function('() => document.getElementById("assembly-receipt").textContent.includes("audit_receipt")',timeout=30000)
            issue=json.loads(page.inner_text('#assembly-receipt'));self.issue_id=issue['id']
            self.case('Chromium source-bound engineering issue candidate',issue['state']=='candidate' and issue['authority_granted'] is False)
            drafts={'chat':['question'],'sources':['docname','version','document','file-version'],
                'review':['rationale'],'memory':['reflection','learning-claim'],'governed':['governed-rationale'],'governance':['central-issuer']}
            for section,fields in drafts.items():
                page.click('[data-view="'+section+'"]')
                for field in fields:page.locator('#'+field).fill('private synthetic draft')
            page.click('#disconnect')
            cleared=page.evaluate('''() => [...document.querySelectorAll('input,textarea,select')].every(n=>n.type==='checkbox'?!n.checked:n.type==='file'?n.files.length===0:n.value==='')''')
            self.case('Chromium logout clears all drafts/file/canvas/token',cleared and page.locator('#pdf-canvas').get_attribute('width')=='0' and page.inner_text('#identity')=='Disconnected')
            self.connect(page,'reviewer');page.click('[data-view="governed"]');page.click('#load-governed')
            card=page.locator('#governed-records .card').filter(has_text=self.issue_id)
            card.get_by_role('button',name='Inspect source-bound payload').click()
            page.wait_for_function('() => document.getElementById("governed-detail").textContent.includes("source_sha256")',timeout=30000)
            page.fill('#governed-rationale','Independent synthetic reviewer checked the exact original source and unverified proposal.')
            card=page.locator('#governed-records .card').filter(has_text=self.issue_id)
            card.get_by_role('button',name='Review candidate',exact=True).click()
            page.wait_for_function('() => document.getElementById("notice").textContent.includes("record reviewed")',timeout=30000)
            self.case('Chromium independently inspect/review governed candidate',True)
            page.click('#disconnect');self.connect(page,'admin');page.click('[data-view="governance"]');page.click('#load-policy')
            page.wait_for_function('() => document.getElementById("policy-data").textContent.includes("daily_call_limit")')
            current=int(page.input_value('#daily-limit'));page.fill('#daily-limit',str(current+1));page.click('#save-policy')
            page.wait_for_function('() => document.getElementById("policy-action-receipt").textContent.includes("pending-independent-review")',timeout=30000)
            action=json.loads(page.inner_text('#policy-action-receipt'));self.action_id=action['action_id']
            page.wait_for_function('(expected) => Number(document.getElementById("daily-limit").value)===expected',arg=current,timeout=30000)
            self.case('Chromium admin sensitive increase stages only',action['policy_unchanged'] and int(page.input_value('#daily-limit'))==current)
            page.click('#disconnect');self.connect(page,'reviewer');page.click('[data-view="governed"]');page.click('#load-actions')
            action_card=page.locator('#policy-actions .card').filter(has_text=self.action_id)
            action_card.get_by_role('button',name='Approve independent action',exact=True).click()
            page.wait_for_function('() => document.getElementById("policy-action-receipt").textContent.includes("applied")',timeout=30000)
            self.case('Chromium reviewer applies pending action independently',True)
            self.case('Chromium no uncaught page errors',not errors,errors)
            browser.close()
    def fingerprint(self,db):
        names=self.sql(db,"SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;").splitlines()
        tables={}
        for name in names:
            if not re.fullmatch(r'[a-z_][a-z0-9_]*',name):raise ValueError('Unexpected table identifier')
            content=self.sql(db,'SELECT to_jsonb(t)::text FROM public.'+name+' t ORDER BY to_jsonb(t)::text;')
            tables[name]=dict(rows=len(content.splitlines()),sha256=hashlib.sha256(content.encode()).hexdigest())
        sections={
            'indexes':"SELECT pg_get_indexdef(indexrelid) FROM pg_index JOIN pg_class c ON c.oid=indrelid JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' ORDER BY pg_get_indexdef(indexrelid);",
            'triggers':"SELECT pg_get_triggerdef(t.oid) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND NOT t.tgisinternal ORDER BY pg_get_triggerdef(t.oid);",
            'relation_acl':"SELECT c.relname,coalesce(grantee.rolname,'PUBLIC'),grantor.rolname,a.privilege_type,a.is_grantable FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace CROSS JOIN LATERAL aclexplode(coalesce(c.relacl,acldefault((CASE WHEN c.relkind='S' THEN 'S' ELSE 'r' END)::\"char\",c.relowner))) a LEFT JOIN pg_roles grantee ON grantee.oid=a.grantee JOIN pg_roles grantor ON grantor.oid=a.grantor WHERE n.nspname='public' AND c.relkind IN ('r','S','v','m','f') ORDER BY 1,2,3,4,5;",
            'column_acl':"SELECT c.relname,col.attname,coalesce(grantee.rolname,'PUBLIC'),grantor.rolname,a.privilege_type,a.is_grantable FROM pg_attribute col JOIN pg_class c ON c.oid=col.attrelid JOIN pg_namespace n ON n.oid=c.relnamespace CROSS JOIN LATERAL aclexplode(col.attacl) a LEFT JOIN pg_roles grantee ON grantee.oid=a.grantee JOIN pg_roles grantor ON grantor.oid=a.grantor WHERE n.nspname='public' AND col.attnum>0 ORDER BY 1,2,3,4,5,6;",
            'function_acl':"SELECT p.proname,pg_get_function_identity_arguments(p.oid),coalesce(grantee.rolname,'PUBLIC'),grantor.rolname,a.privilege_type,a.is_grantable FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace CROSS JOIN LATERAL aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a LEFT JOIN pg_roles grantee ON grantee.oid=a.grantee JOIN pg_roles grantor ON grantor.oid=a.grantor WHERE n.nspname='public' ORDER BY 1,2,3,4,5,6;",
            'schema_acl':"SELECT n.nspname,coalesce(grantee.rolname,'PUBLIC'),grantor.rolname,a.privilege_type,a.is_grantable FROM pg_namespace n CROSS JOIN LATERAL aclexplode(coalesce(n.nspacl,acldefault('n',n.nspowner))) a LEFT JOIN pg_roles grantee ON grantee.oid=a.grantee JOIN pg_roles grantor ON grantor.oid=a.grantor WHERE n.nspname='public' ORDER BY 1,2,3,4,5;",
            'database_acl':"SELECT d.datname,coalesce(grantee.rolname,'PUBLIC'),grantor.rolname,a.privilege_type,a.is_grantable FROM pg_database d CROSS JOIN LATERAL aclexplode(coalesce(d.datacl,acldefault('d',d.datdba))) a LEFT JOIN pg_roles grantee ON grantee.oid=a.grantee JOIN pg_roles grantor ON grantor.oid=a.grantor WHERE d.datname='nsai' ORDER BY 1,2,3,4,5;",
            'role_attributes':"SELECT rolname,rolcanlogin,rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls FROM pg_roles WHERE rolname IN ('nsai_app','nsai_extra') ORDER BY rolname; SELECT parent.rolname,member.rolname,m.admin_option FROM pg_auth_members m JOIN pg_roles parent ON parent.oid=m.roleid JOIN pg_roles member ON member.oid=m.member WHERE member.rolname IN ('nsai_app','nsai_extra') ORDER BY 1,2,3;"
        }
        definitions={name:self.sql(db,sql) for name,sql in sections.items()}
        return dict(tables=tables,definitions=definitions,definition_hashes={name:hashlib.sha256(value.encode()).hexdigest() for name,value in definitions.items()})
    def cleanup(self):
        cleanup=[]
        for name in reversed(self.containers):
            inspect=subprocess.run(['docker','inspect',name],capture_output=True)
            if inspect.returncode:continue
            data=json.loads(inspect.stdout)[0]
            if data['Config'].get('Labels',{}).get('nsai.owner')!=self.tag:raise RuntimeError('Refused cleanup of unowned container')
            result=subprocess.run(['docker','rm','-f',name],capture_output=True);cleanup.append(dict(container=name,removed=result.returncode==0))
        for name in reversed(self.networks):
            inspect=subprocess.run(['docker','network','inspect',name],capture_output=True)
            if inspect.returncode:continue
            data=json.loads(inspect.stdout)[0]
            if data.get('Labels',{}).get('nsai.owner')!=self.tag:raise RuntimeError('Refused cleanup of unowned network')
            result=subprocess.run(['docker','network','rm',name],capture_output=True);cleanup.append(dict(network=name,removed=result.returncode==0))
        self.receipt['cleanup']=cleanup
        self.receipt['cleanup_complete']=all(entry['removed'] for entry in cleanup)
        self.save()
    def capture_identity(self):
        policies=[];model_images=set()
        for name in self.containers:
            data=json.loads(command(['docker','inspect',name]))[0]
            types=[]
            for network in data.get('NetworkSettings',{}).get('Networks',{}):
                info=json.loads(command(['docker','network','inspect',network]))[0]
                types.append('internal' if info.get('Internal') else 'bridge')
                if network=='amd-hackathon-nsai_model_net':
                    for member in info.get('Containers',{}):
                        target=json.loads(command(['docker','inspect',member]))[0]
                        if target['Config'].get('Labels',{}).get('com.docker.compose.service')=='llama-cpp':
                            model_images.add(target['Image'])
            policy=public_runtime_policy(data,types)
            policy['role']=name.removeprefix(self.prefix+'-')
            policies.append(policy)
        if len(model_images)!=1 or not policies:
            raise RuntimeError('Exact model/runtime identity unavailable')
        self.receipt['effective_owned_policy']=dict(services=sorted(policies,key=lambda p:p['role']),model_image_digest=next(iter(model_images)))
        self.receipt['identity_capture_complete']=True
    def save_identity(self):
        raw=(self.output/'receipt.json').read_bytes()
        producer={name:hashlib.sha256((ROOT/'scripts'/name).read_bytes()).hexdigest() for name in ('qualify_local_stack.py','migrate.py','evidence_contract.py')}
        identity=dict(run_id=self.run_id,source_sha256=identity_hash(self.before),image_digest=self.api_image,
                      effective_config_sha256=identity_hash(self.receipt.get('effective_owned_policy',{})),producer_sha256=identity_hash(producer))
        sidecar=stack_envelope(raw,identity)
        sidecar['identity']=identity
        sidecar['source_manifest']=self.before
        sidecar['producer_manifest']=producer
        (self.output/'identity.json').write_text(json.dumps(sidecar,indent=2),encoding='utf-8')
    def execute(self):
        spec=importlib.util.spec_from_file_location('qualified_migrate',ROOT/'scripts/migrate.py');migrate=importlib.util.module_from_spec(spec);spec.loader.exec_module(migrate)
        try:
            with tempfile.TemporaryDirectory(prefix=self.prefix+'-') as folder:
                directory=Path(folder);snapshot=directory/'snapshot';snapshot.mkdir()
                for name in ('src','assets'):shutil.copytree(ROOT/name,snapshot/name,ignore=shutil.ignore_patterns('__pycache__'))
                self.case('Current source snapshot stable at copy',source_hashes()==self.before)
                secret_dir=directory/'secrets';secret_dir.mkdir();self.tokens={role:secrets.token_hex(32) for role in ('operator','reviewer','admin','viewer','parser','ocr','db')}
                for role,value in self.tokens.items():(secret_dir/(role+'.txt')).write_text(value,encoding='utf-8')
                dbnet=self.network('db');parsernet=self.network('parser');ocrnet=self.network('ocr');appnet=self.network('app',internal=False);db=self.db('db',dbnet,secrets.token_hex(32))
                self.sql(db,migrate.migration_sql(ROOT)+'COMMIT;')
                self.sql(db,"CREATE ROLE nsai_extra NOLOGIN; CREATE ROLE nsai_app LOGIN PASSWORD '"+self.tokens['db']+"' SUPERUSER CREATEDB CREATEROLE REPLICATION BYPASSRLS; GRANT nsai_extra TO nsai_app; GRANT CREATE ON SCHEMA public TO nsai_app;")
                self.sql(db,'BEGIN;'+migrate.role_sql(self.tokens['db'],include_commit=False)+'COMMIT;')
                attrs=self.sql(db,"SELECT rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls FROM pg_roles WHERE rolname='nsai_app'; SELECT count(*) FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.member WHERE r.rolname='nsai_app';").splitlines()
                self.case('Migration converges seeded excess role attributes/memberships',attrs==['f|f|f|f|f','0'])
                base_mount=['--mount',f'type=bind,source={snapshot},target=/qualified,readonly','--mount',f'type=bind,source={secret_dir},target=/qualification-secrets,readonly','--env','PYTHONPATH=/qualified/src']
                parser_mount=['--mount',f'type=bind,source={snapshot},target=/qualified,readonly','--mount',f'type=bind,source={secret_dir / "parser.txt"},target=/run/secrets/parser_token,readonly','--env','PYTHONPATH=/qualified/src','--env','NSAI_PARSER_TOKEN_FILE=/run/secrets/parser_token']
                parser=self.run('parser',self.api_image,parser_mount,['uvicorn','nsai.parser:app','--host','0.0.0.0','--port','8788','--no-access-log'],network=parsernet,alias='parser',memory='384m',pids='32')
                ocr=self.run('ocr',self.ocr_image,['--mount',f'type=bind,source={secret_dir / "ocr.txt"},target=/run/secrets/ocr_token,readonly','--env','NSAI_OCR_TOKEN_FILE=/run/secrets/ocr_token'],network=ocrnet,alias='ocr',user='10002:10002')
                env={'NSAI_DB_HOST':'db','NSAI_DB_NAME':'nsai','NSAI_DB_USER':'nsai_app','NSAI_DB_PASSWORD_FILE':'/qualification-secrets/db.txt',
                    'NSAI_API_TOKEN_FILE':'/qualification-secrets/operator.txt','NSAI_REVIEWER_TOKEN_FILE':'/qualification-secrets/reviewer.txt','NSAI_ADMIN_TOKEN_FILE':'/qualification-secrets/admin.txt','NSAI_VIEWER_TOKEN_FILE':'/qualification-secrets/viewer.txt',
                    'NSAI_PARSER_URL':'http://parser:8788','NSAI_PARSER_TOKEN_FILE':'/qualification-secrets/parser.txt','NSAI_OCR_URL':'http://ocr:8091','NSAI_OCR_TOKEN_FILE':'/qualification-secrets/ocr.txt',
                    'NSAI_CENTRAL_SECURITY_ENABLED':'false','NSAI_MODEL_URL':'http://llama-cpp:8080/v1','NSAI_MODEL_NAME':'nsai-local-qwen','NSAI_MODEL_PROVIDER':'local-llamacpp-cpu','NSAI_MODEL_API_KEY_FILE':'/run/secrets/model_token','NSAI_MODEL_CONTEXT_TOKENS':'8192'}
                options=base_mount+['--publish','127.0.0.1::8787','--mount',f'type=bind,source={ROOT / "secrets/model_token.txt"},target=/run/secrets/model_token,readonly']
                for key,value in env.items():options+=['--env',key+'='+value]
                api=self.run('api',self.api_image,options,['uvicorn','nsai.api:app','--host','0.0.0.0','--port','8787','--no-access-log'],network=appnet)
                for network in (dbnet,parsernet,ocrnet,'amd-hackathon-nsai_model_net'):command(['docker','network','connect',network,api])
                info=json.loads(command(['docker','inspect',api]))[0];ports=info['NetworkSettings']['Ports']['8787/tcp']
                self.case('Only owned API exposes ephemeral loopback port',len(ports)==1 and ports[0]['HostIp']=='127.0.0.1',ports)
                self.base='http://127.0.0.1:'+ports[0]['HostPort']
                for _ in range(60):
                    try:
                        if self.http('/readyz')[0]==200:break
                    except (OSError,urllib.error.URLError):pass
                    time.sleep(.25)
                else:raise RuntimeError('Owned API readiness deadline exceeded')
                self.case('Real API/readiness and anonymous auth denial',self.http('/readyz')[0]==200 and self.http('/v1/documents')[0]==401)
                self.case('Private static receipt denied for GET and HEAD',all(self.http('/assets/verification.json',method=method)[0]==404 for method in ('GET','HEAD')))
                aliases=('/assets/%2e/verification.json','/assets/x/%2e%2e/verification.json','/assets//verification.json','/assets/VERIFICATION.JSON','/assets/verification.json::$DATA')
                alias_status={path:{method:self.http(path,method=method)[0] for method in ('GET','HEAD')} for path in aliases}
                self.case('Private receipt path aliases denied GET and HEAD',all(code==404 for statuses in alias_status.values() for code in statuses.values()),alias_status)
                self.case('Public PDF module and worker remain available',all(self.http(path)[0]==200 for path in ('/assets/pdfjs/pdf.mjs','/assets/pdfjs/pdf.worker.mjs')))
                status,public,_,raw=self.http('/v1/submission/evidence','operator')
                decoded=raw.decode('utf-8')
                private_patterns=(r'[A-Za-z]:[\\/]',r'/(?:app|qualified|tmp|home|Users)/',r'nsai-qual-stack-',r'private synthetic draft')
                self.case('Authenticated summary has no absolute paths or private canaries',status==200 and isinstance(public,dict) and not any(re.search(pattern,decoded,re.I) for pattern in private_patterns),dict(status=status,summary_sha256=hashlib.sha256(raw).hexdigest(),summary_bytes=len(raw)))
                for role in ('operator','reviewer','admin','viewer'):
                    status,data,_,_=self.http('/v1/capabilities',role);self.case('Real role identity '+role,status==200 and data['identity']['role']==role)
                self.case('Real viewer write denial',self.http('/v1/documents','viewer','POST',dict(title='Forbidden',version='1',text='Never inserted'))[0]==403)
                self.case('Generated execution remains denied',all(self.http('/v1/execute',role,'POST',{})[0]==403 for role in ('operator','reviewer','admin','viewer')))
                status,source,_,_=self.http('/v1/documents','operator','POST',dict(title='Original synthetic engineering notes',version='1',text='Pump-X maximum operating temperature is 75 C.\nMeasured reading is 74 C.\nInspect the inlet before restarting.'))
                self.case('Real source ingestion candidate',status==200 and source['created']);self.native_doc=source['document_id']
                self.browser(ROOT/'evidence/implementation/ocr-calibration/inputs/000.pdf')
                status,policy,_,_=self.http('/v1/admin/security','admin');policy=policy['policy']
                payload={key:policy[key] for key in ('inference_enabled','daily_call_limit','central_config')};payload.update(expected_revision=policy['revision'],max_output_tokens=50)
                self.case('Owned output budget lowered before inference',self.http('/v1/admin/policy','admin','PUT',payload)[0]==200)
                status,result,_,_=self.http('/v1/reason','operator','POST',dict(question='What is the maximum temperature? Answer briefly.',document_ids=[self.native_doc],revision='1',request_id=uuid4().hex))
                self.case('One real CPU inference through owned application',status==200 and result.get('run_id') and result.get('token_admission',{}).get('admitted') and not result.get('answer_verified'),dict(status=status,**{key:result.get(key) for key in ('mode','answer','conflicts','usage','token_admission','run_id','audit_receipt')}))
                self.case('Actual admitted CPU context is commissioned 8192 tokens',result.get('token_admission',{}).get('context_tokens')==8192,result.get('token_admission'))
                self.case('Exactly one owned inference attempt persisted',self.sql(db,'SELECT count(*) FROM inference_runs;').strip()=='1')
                status,audit,_,_=self.http('/v1/audit','reviewer');self.case('Owned audit chain fresh validation',status==200 and audit.get('valid'),audit)
                before=self.fingerprint(db)
                backup=self.output/'owned-backup.sql'
                migrate.stream_backup(['docker','exec',db,'pg_dump','-U','nsai','-d','nsai'],backup)
                restore=self.db('restore',dbnet,secrets.token_hex(32))
                self.sql(restore,"CREATE ROLE nsai_extra NOLOGIN; CREATE ROLE nsai_app LOGIN PASSWORD '"+self.tokens['db']+"' NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;")
                self.sql(restore,backup.read_text())
                # Plain pg_dump does not capture database-level ACL or global
                # role policy. Apply the exact production privilege contract.
                self.sql(restore,'BEGIN;'+migrate.role_sql(self.tokens['db'],include_commit=False)+'COMMIT;')
                after=self.fingerprint(restore)
                self.case('Actual dump/restore rows indexes triggers and ACL identity',before==after,dict(original=before,restored=after,backup_sha256=hashlib.sha256(backup.read_bytes()).hexdigest()))
                self.receipt['sources_after']=source_hashes();self.case('Host source/configuration unchanged across qualification',self.before==self.receipt['sources_after'])
                self.receipt.update(status='PASS',completed_at=datetime.now(timezone.utc).isoformat(),qualification='Owned candidate integration only; synthetic OCR limits and dedicated security-scan blocker remain separate',model_calls=1,production_application_db_touched=False)
        except Exception as error:
            self.receipt.update(status='FAIL',failure_type=type(error).__name__,failure=str(error));self.save();raise
        finally:
            try:
                self.capture_identity()
            except Exception as error:
                self.receipt['identity_capture_complete']=False
                self.receipt['identity_capture_failure_type']=type(error).__name__
            try:
                self.cleanup()
            except Exception as error:
                self.receipt['cleanup_complete']=False
                self.receipt['cleanup_failure_type']=type(error).__name__
                raise
            finally:
                # Preserve failure bytes; no PASS sidecar if cleanup raises or sources drift.
                self.receipt['sources_after']=source_hashes()
                if (self.receipt.get('cleanup_complete') is not True or self.before!=self.receipt['sources_after'] or
                    self.receipt.get('identity_capture_complete') is not True or not self.cases or
                    not all(case.get('pass_') is True for case in self.cases)):
                    self.receipt['status']='FAIL'
                self.save()
                self.save_identity()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=Path('evidence/implementation/stack-qualification'));parser.add_argument('--db-image',default='nsai-db-package-qualified:local');parser.add_argument('--ocr-image',default='nsai-ocr-hardened-candidate:local');args=parser.parse_args()
    stack=Stack(args.output,args.db_image,args.ocr_image)
    try:stack.execute()
    finally:print(json.dumps(dict(status=stack.receipt['status'],cases=len(stack.cases),cleanup=stack.receipt.get('cleanup_complete'))),flush=True)
    try:
        sidecar=json.loads((stack.output/'identity.json').read_bytes())
        raw=(stack.output/'receipt.json').read_bytes()
        admission=admit_receipt(sidecar['receipt'],raw,sidecar['identity'])
        return 0 if (stack.receipt.get('status')=='PASS' and stack.receipt.get('cleanup_complete') is True
                     and stack.receipt.get('identity_capture_complete') is True and admission['status']=='PASS_SCOPED') else 1
    except (OSError,ValueError,KeyError,TypeError):
        return 1

if __name__=='__main__':raise SystemExit(main())
