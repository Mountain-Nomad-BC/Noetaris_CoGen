"""Run the owned real-service grounded application fixture; never live services."""
import argparse
import hashlib
import json
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import time
import urllib.request
import traceback
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import migrate
from check_release_readiness import source_snapshot
from qualify_local_stack import Stack
from qualify_cpu_grounded_smoke import LLAMA,REVISION,MODEL_SHA
from prepare_cpu_model import verify_model

OCR_FIXTURE=ROOT/'evidence/ocr-geometry-requalification/6115e87c2baf4737b6f639bac749ae55'


def main():
    arguments=argparse.ArgumentParser(description=__doc__)
    arguments.add_argument('--model-storage',choices=['owned-volume','host-bind'],default='owned-volume')
    arguments.add_argument('--model-cpus',type=int,choices=[1,6],default=6)
    arguments.add_argument('--browser-dpr',type=int,choices=[1,2,3],default=1)
    arguments.add_argument('--ocr-fixture',type=Path,default=OCR_FIXTURE)
    arguments.add_argument('--upload-profile',choices=['default','standard-evaluation'],default='default')
    arguments.add_argument('--operation-coordination',action='store_true')
    args=arguments.parse_args()
    ocr_fixture=args.ocr_fixture.resolve()
    assert ocr_fixture.is_relative_to((ROOT/'evidence').resolve())
    ocr_manifest=json.loads((ocr_fixture/'frozen-manifest.json').read_bytes())
    assert hashlib.sha256((ocr_fixture/'original-raster.pdf').read_bytes()).hexdigest()==ocr_manifest['pdf_sha256']
    upload_env=['-e','NSAI_UPLOAD_PROFILE='+args.upload_profile]
    owner=uuid4().hex;folder=ROOT/'evidence/grounded-application'/owner
    stack=Stack(folder,'nsai-db-package-qualified:local','nsai-ocr-hardened-candidate:local')
    fixtures=[Path(__file__),ROOT/'tests/grounded_runtime_fixture.py',ROOT/'tests/semantic_fixture_helpers.py',
              ocr_fixture/'original-raster.pdf',ocr_fixture/'frozen-manifest.json']
    def hashes():return {path.name:hashlib.sha256(path.read_bytes()).hexdigest() for path in fixtures}
    report=dict(status='FAIL',run_id=owner,scope=__doc__,source_before=source_snapshot(ROOT),fixture_before=hashes(),
        host_ports=True,loopback_only=True,live_services_accessed=False,private_http_admitted=False,
        model_scope='Pinned 1.5B evaluation model; live model unchanged; no held-out acceptance',upload_profile=args.upload_profile)
    def command(args,*,ok=True,timeout=30):
        result=subprocess.run(['docker',*args],capture_output=True,timeout=timeout)
        if ok and result.returncode:raise RuntimeError('Owned grounded application command failed')
        return result
    model_volume=None
    try:
        model_path=ROOT/'state/models/qwen2.5-1.5b-instruct-evaluation'/REVISION/'qwen2.5-1.5b-instruct-q4_k_m.gguf'
        report['model']=verify_model(model_path,MODEL_SHA)
        model_mount='type=bind,source='+str(model_path)+',target=/models/model.gguf,readonly'
        if args.model_storage=='owned-volume':
            candidate_volume=stack.prefix+'-model-data'
            assert command(['volume','inspect',candidate_volume],ok=False).returncode!=0
            command(['volume','create','--label','nsai.owner='+stack.tag,candidate_volume])
            metadata=json.loads(command(['volume','inspect',candidate_volume]).stdout)[0]
            assert metadata['Labels'].get('nsai.owner')==stack.tag
            model_volume=candidate_volume
            stage_program="""import hashlib,json,os
h=hashlib.sha256();size=0
with open('/seed/model.gguf','rb') as source,open('/evaluation-model/model.gguf','xb') as target:
 while block:=source.read(1024*1024):
  h.update(block);size+=len(block);target.write(block)
 target.flush();os.fsync(target.fileno())
print(json.dumps(dict(sha256=h.hexdigest(),bytes=size)))
"""
            staged_at=time.monotonic()
            staging=stack.run('model-stage',stack.api_image,['--network','none',
                '--mount','type=bind,source='+str(model_path)+',target=/seed/model.gguf,readonly',
                '--mount','type=volume,source='+model_volume+',target=/evaluation-model','--entrypoint','python'],
                ['-c',stage_program],user='0:0',memory='192m',pids='16')
            while command(['inspect',staging,'--format','{{.State.Running}}']).stdout.strip()==b'true':
                if time.monotonic()-staged_at>180:raise TimeoutError('Owned public-model staging deadline')
                time.sleep(.5)
            output=command(['logs',staging],ok=False)
            (folder/'model-stage-output.json').write_bytes(output.stdout);(folder/'model-stage-errors.txt').write_bytes(output.stderr)
            assert command(['inspect',staging,'--format','{{.State.ExitCode}}']).stdout.strip()==b'0'
            staged=json.loads(output.stdout);assert staged['sha256']==MODEL_SHA and staged['bytes']==1117320736
            report['model_storage']=dict(kind='owned-volume',**staged,staging_seconds=time.monotonic()-staged_at,
                staging_scope='Public evaluation weights only; root staging helper has no capabilities/network and writes only its owned volume',
                file_cache='Staging primes cache; no cold-cache startup or storage qualification claimed')
            model_mount='type=volume,source='+model_volume+',target=/models,readonly'
        else:report['model_storage']=dict(kind='host-bind',sha256=MODEL_SHA)
        encoder_image=command(['image','inspect','nsai-cpu-encoder:qualification','--format','{{.Id}}']).stdout.decode().strip()
        report['images']=dict(api=stack.api_image,db=stack.db_image,encoder=encoder_image,model=LLAMA,ocr=stack.ocr_image)
        data_net=stack.network('data');encoder_net=stack.network('encoder');model_net=stack.network('model');parser_net=stack.network('parser');ocr_net=stack.network('ocr')
        with tempfile.TemporaryDirectory(prefix='nsai-grounded-app-') as temporary:
            temporary=Path(temporary);password=secrets.token_hex(32);application_password=secrets.token_hex(32)
            for name,value in [('db',application_password),('encoder',secrets.token_hex(32)),('parser',secrets.token_hex(32)),
                               ('model',secrets.token_hex(32)),('operator',secrets.token_hex(32)),('admin',secrets.token_hex(32)),
                               ('viewer',secrets.token_hex(32)),('reviewer',secrets.token_hex(32)),('ocr',secrets.token_hex(32)),('private-user',secrets.token_hex(32))]:
                (temporary/name).write_text(value,encoding='utf-8')
            (temporary/'identities').write_text(json.dumps(dict(schema_version='nsai.local-identities/1',identities=[
                dict(actor='local-user-browser',role='operator',token_file='/run/secrets/private-user')])),encoding='utf-8')
            def secret(name):return ['--mount','type=bind,source='+str(temporary/name)+',target=/run/secrets/'+name+',readonly']
            db=stack.run('db',stack.db_image,['--tmpfs','/var/lib/postgresql/data:rw,nosuid,nodev,size=512m,mode=1777',
                '--tmpfs','/var/run/postgresql:rw,nosuid,nodev,size=8m,mode=1777','-e','POSTGRES_USER=nsai',
                '-e','POSTGRES_DB=nsai','-e','POSTGRES_PASSWORD='+password,'-e','PGDATA=/var/lib/postgresql/data/pgdata'],
                network=data_net,alias='db',user='70:70',memory='768m',pids='128')
            for _ in range(120):
                if command(['exec',db,'pg_isready','-h','127.0.0.1','-U','nsai'],ok=False).returncode==0:break
                time.sleep(.1)
            else:raise RuntimeError('Owned grounded database readiness deadline')
            stack.sql(db,migrate.migration_sql(ROOT)+migrate.role_sql(application_password))
            encoder=stack.run('encoder',encoder_image,[*secret('encoder'),'-e','NSAI_ENCODER_TOKEN_FILE=/run/secrets/encoder',
                '-e','NSAI_ENCODER_MODEL_DIR=/models','--mount','type=bind,source='+str(ROOT/'state/models/all-MiniLM-L6-v2')+',target=/models,readonly',
                '--entrypoint','uvicorn'],['nsai.encoder_service:app','--host','0.0.0.0','--port','8092','--no-access-log'],
                network=encoder_net,alias='encoder',memory='768m',pids='128')
            model=stack.prefix+'-model'
            command(['run','-d','--name',model,'--label','nsai.owner='+stack.tag,'--network',model_net,
                '--network-alias','llama-cpp','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges:true',
                '--user','10001:10001','--cpus',str(args.model_cpus),'--memory','4g','--pids-limit','128',
                '--tmpfs','/tmp:rw,noexec,nosuid,size=128m',*secret('model'),'--mount',model_mount,LLAMA,
                '-m','/models/model.gguf','--alias','nsai-local-qwen','--host','0.0.0.0','--port','8080',
                '--ctx-size','4096','--parallel','1','--threads',str(args.model_cpus),'--threads-batch',str(args.model_cpus),
                '--n-gpu-layers','0','--no-ui','--no-agent','--no-slots','--api-key-file','/run/secrets/model','--timeout','125'])
            stack.containers.append(model)
            model_configuration=json.loads(command(['inspect',model]).stdout)[0]['HostConfig']
            assert model_configuration['NanoCpus']==args.model_cpus*1000000000 and model_configuration['Memory']==4*1024**3
            report['model_resources']=dict(cpus=args.model_cpus,decode_threads=args.model_cpus,prefill_threads=args.model_cpus,
                memory_bytes=model_configuration['Memory'],context_tokens=4096,
                scope='Owned 1.5B evaluation profile; live model/CPU settings unchanged; no other CPU profile accepted')
            for _ in range(120):
                probe="import urllib.request;urllib.request.urlopen('http://127.0.0.1:8092/healthz',timeout=2)"
                if command(['exec',encoder,'python','-c',probe],ok=False).returncode==0:break
                time.sleep(.25)
            else:raise RuntimeError('Owned grounded encoder readiness deadline')
            client=stack.prefix+'-client'
            command(['create','--name',client,'--label','nsai.owner='+stack.tag,'--network',data_net,
                '--read-only','--cap-drop','ALL','--security-opt','no-new-privileges:true','--user','10001:10001',
                '--cpus','1','--memory','768m','--pids-limit','128','--tmpfs','/tmp:rw,nosuid,nodev,noexec,size=64m,mode=1777',
                *secret('db'),*secret('encoder'),*secret('model'),*secret('operator'),*secret('admin'),
                '--mount','type=bind,source='+str(ROOT/'tests/grounded_runtime_fixture.py')+',target=/qualification.py,readonly',
                '--mount','type=bind,source='+str(ROOT/'tests/semantic_fixture_helpers.py')+',target=/semantic_fixture_helpers.py,readonly',
                '-e','NSAI_DB_HOST=db','-e','NSAI_DB_USER=nsai_app','-e','NSAI_DB_NAME=nsai','-e','NSAI_DB_PASSWORD_FILE=/run/secrets/db',
                '-e','NSAI_API_TOKEN_FILE=/run/secrets/operator','-e','NSAI_ADMIN_TOKEN_FILE=/run/secrets/admin',
                '-e','NSAI_ENCODER_URL=http://encoder:8092','-e','NSAI_ENCODER_TOKEN_FILE=/run/secrets/encoder',
                '-e','NSAI_MODEL_URL=http://llama-cpp:8080/v1','-e','NSAI_MODEL_NAME=nsai-local-qwen',
                '-e','NSAI_MODEL_PROVIDER=owned-cpu-evaluation','-e','NSAI_MODEL_API_KEY_FILE=/run/secrets/model',
                '--entrypoint','python',stack.api_image,'/qualification.py'])
            stack.containers.append(client)
            command(['network','connect',encoder_net,client]);command(['network','connect',model_net,client]);command(['start',client])
            # Poll rather than holding a tool call across the full workload.
            deadline=time.monotonic()+600
            while command(['inspect',client,'--format','{{.State.Running}}']).stdout.strip()==b'true':
                if time.monotonic()>deadline:raise TimeoutError('Owned grounded application deadline')
                time.sleep(.5)
            output=command(['logs',client],ok=False)
            (folder/'worker-output.json').write_bytes(output.stdout);(folder/'worker-errors.txt').write_bytes(output.stderr)
            assert command(['inspect',client,'--format','{{.State.ExitCode}}']).stdout.strip()==b'0','Application worker failed; diagnostics retained'
            report['result']=json.loads(output.stdout.strip().splitlines()[-1])
            assert report['result']['status']=='PASS_SCOPED'
            parser_server=stack.run('parser',stack.api_image,[*upload_env,*secret('parser'),'-e','NSAI_PARSER_TOKEN_FILE=/run/secrets/parser','--entrypoint','uvicorn'],
                ['nsai.parser:app','--host','0.0.0.0','--port','8788','--no-access-log'],network=parser_net,alias='parser',memory='512m',pids='64')
            ocr_server=stack.run('ocr',stack.ocr_image,[*upload_env,*secret('ocr'),'-e','NSAI_OCR_TOKEN_FILE=/run/secrets/ocr'],
                network=ocr_net,alias='ocr',user='10002:10002',memory='768m',pids='64')
            # A real API process serves the real browser. No API interception,
            # source mounts, live model credentials or production ports are used.
            browser_net=stack.network('browser',internal=False)
            report['browser_network_scope']='Owned bridge permits loopback publication; API egress denial is not qualified'
            api_server=stack.run('api',stack.api_image,[*(['-e','NSAI_OPERATION_COORDINATION=true'] if args.operation_coordination else []),*upload_env,*secret('db'),*secret('encoder'),*secret('model'),*secret('operator'),*secret('admin'),*secret('parser'),*secret('viewer'),*secret('reviewer'),*secret('ocr'),*secret('private-user'),*secret('identities'),
                '-e','NSAI_LOCAL_IDENTITIES_FILE=/run/secrets/identities',
                '--publish','127.0.0.1::8787','-e','NSAI_DB_HOST=db','-e','NSAI_DB_USER=nsai_app','-e','NSAI_DB_NAME=nsai',
                '-e','NSAI_DB_PASSWORD_FILE=/run/secrets/db','-e','NSAI_API_TOKEN_FILE=/run/secrets/operator',
                '-e','NSAI_ADMIN_TOKEN_FILE=/run/secrets/admin','-e','NSAI_ENCODER_URL=http://encoder:8092',
                '-e','NSAI_VIEWER_TOKEN_FILE=/run/secrets/viewer','-e','NSAI_REVIEWER_TOKEN_FILE=/run/secrets/reviewer',
                '-e','NSAI_ENCODER_TOKEN_FILE=/run/secrets/encoder','-e','NSAI_MODEL_URL=http://llama-cpp:8080/v1',
                '-e','NSAI_MODEL_NAME=nsai-local-qwen','-e','NSAI_MODEL_PROVIDER=owned-cpu-evaluation',
                '-e','NSAI_MODEL_API_KEY_FILE=/run/secrets/model','-e','NSAI_INDEX_WORKER_ENABLED=true','-e','NSAI_INDEX_CONCURRENCY=2',
                '-e','NSAI_OCR_URL=http://ocr:8091','-e','NSAI_OCR_TOKEN_FILE=/run/secrets/ocr',
                '-e','NSAI_PARSER_URL=http://parser:8788','-e','NSAI_PARSER_TOKEN_FILE=/run/secrets/parser','--entrypoint','uvicorn'],
                ['nsai.api:app','--host','0.0.0.0','--port','8787','--no-access-log'],network=browser_net,memory='768m',pids='128')
            command(['network','connect',data_net,api_server]);command(['network','connect',encoder_net,api_server]);command(['network','connect',model_net,api_server])
            command(['network','connect',parser_net,api_server])
            command(['network','connect',ocr_net,api_server])
            ports=json.loads(command(['inspect',api_server,'--format','{{json .NetworkSettings.Ports}}']).stdout)['8787/tcp']
            report['api_ports']=ports
            assert len(ports)==1 and ports[0]['HostIp']=='127.0.0.1','Owned API must publish exactly one loopback binding'
            base='http://127.0.0.1:'+ports[0]['HostPort']
            report['browser_origin']=base
            for _ in range(120):
                try:
                    with urllib.request.urlopen(base+'/readyz',timeout=2) as response:
                        if response.status==200:break
                except (OSError,TimeoutError):pass
                time.sleep(.25)
            else:raise RuntimeError('Owned browser API readiness deadline')
            from playwright.sync_api import sync_playwright
            with sync_playwright() as playwright:
                browser=playwright.chromium.launch(headless=True)
                context=browser.new_context(device_scale_factor=args.browser_dpr);page=context.new_page()
                errors=[];external=[]
                page.on('pageerror',lambda error:errors.append(str(error)))
                page.on('request',lambda request:external.append(request.url) if not request.url.startswith((base+'/', 'data:', 'blob:')) else None)
                def login(role):
                    page.fill('#token',(temporary/role).read_text(encoding='utf-8'));page.click('#connect')
                    page.wait_for_function('(role) => document.getElementById("identity").textContent.includes(role)',arg=role,timeout=30000)
                    page.wait_for_function("() => !document.getElementById('connect').disabled",timeout=30000)
                page.goto(base,wait_until='networkidle')
                login('operator')
                envelope=page.evaluate('''async () => {
                    const headers={Authorization:'Bearer '+token};
                    const caps=await (await fetch('/v1/capabilities',{headers})).json();
                    const before=await (await fetch('/v1/documents',{headers})).json();
                    const form=new FormData();form.append('file',new Blob([new Uint8Array(caps.upload_limits.max_bytes+1)]),'over-envelope.pdf');
                    form.append('version','boundary-rejection');
                    const rejected=await fetch('/v1/files',{method:'POST',headers,body:form});
                    const after=await (await fetch('/v1/documents',{headers})).json();
                    return {limits:caps.upload_limits,status:rejected.status,before:before.total,after:after.total};
                }''')
                assert envelope['limits']['profile']==args.upload_profile and envelope['status']==413
                assert isinstance(envelope['before'],int) and envelope['before']==envelope['after']
                assert page.locator('#upload-limits').inner_text().find(str(envelope['limits']['max_pages']))>=0
                report['oversized_upload_boundary']=dict(**envelope,library_count_unchanged=True)
                page.wait_for_function("() => !document.getElementById('model').disabled",timeout=30000)
                page.click('[data-view="sources"]')
                page.locator('#documents .card').filter(has_text='Motor-Y original').get_by_role('button',name='Inspect source & manifest').click()
                page.wait_for_function("() => document.getElementById('source-inspector').textContent.includes('Motor-Y original')",timeout=30000)
                page.select_option('#chat-scope','document')
                page.fill('#question','What is the maximum operating temperature of Motor-Y?')
                with page.expect_response(lambda response:response.url.endswith('/v1/reason') and response.request.method=='POST',timeout=180000) as pending:
                    page.click('#model')
                response=pending.value;answer=response.json();payload=response.request.post_data_json
                assert response.status==200 and answer['mode']=='model_unverified' and '85' in answer['answer']
                target=report['result']['answers'][1]['result']['citations'][0]['document_id']
                assert payload['document_ids']==[target] and payload['revision']=='grounded-1'
                assert answer['citations'] and all(citation['document_id']==target for citation in answer['citations'])
                page.wait_for_function("() => document.querySelector('#feed .assistant')?.textContent.includes('85')",timeout=30000)
                assert 'PRIVATE-GROUNDED-CANARY' not in page.locator('body').inner_text()
                page.locator('#feed .assistant .citation').first.click()
                expected=hashlib.sha256(b'Motor-Y maximum operating temperature is 85 C.').hexdigest()
                page.wait_for_function('(digest) => document.getElementById("source-inspector").textContent.includes(digest)',arg=expected,timeout=30000)
                page.screenshot(path=str(folder/'grounded-browser.png'),full_page=True)
                # A new generated original traverses browser upload, actual
                # parser, durable worker publication and citation rendering.
                from io import BytesIO
                from pypdf import PdfWriter
                from pypdf.generic import DictionaryObject,NameObject,DecodedStreamObject
                writer=PdfWriter();pdf_page=writer.add_blank_page(width=612,height=792)
                font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
                pdf_page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):writer._add_object(font)})})
                content=DecodedStreamObject();content.set_data(b'BT /F1 12 Tf 60 730 Td (Motor-Q maximum operating temperature is 65 C.) Tj 0 -24 Td (E = m*c^2.) Tj ET')
                pdf_page[NameObject('/Contents')]=writer._add_object(content)
                if args.upload_profile=='standard-evaluation':
                    for _ in range(249):writer.add_blank_page(width=612,height=792)
                    # Sparse native envelope, deliberately not a dense-content qualification.
                    last=writer.pages[-1]
                    last[NameObject('/Resources')]=pdf_page['/Resources']
                    tail=DecodedStreamObject();tail.set_data(b'BT /F1 12 Tf 60 730 Td (Motor-Envelope maximum operating temperature is 75 C.) Tj ET')
                    last[NameObject('/Contents')]=writer._add_object(tail)
                    padding=DecodedStreamObject();padding.set_data(b'x')
                    writer._add_object(padding)
                    for _ in range(5):
                        trial=BytesIO();writer.write(trial)
                        delta=25*1024*1024-len(trial.getvalue())
                        if delta==0:break
                        padding.set_data(b'x'*(len(padding._data)+delta))
                buffer=BytesIO();writer.write(buffer);pdf_bytes=buffer.getvalue()
                if args.upload_profile=='standard-evaluation':assert len(pdf_bytes)==25*1024*1024
                report['browser_pdf_fixture']=dict(bytes=len(pdf_bytes),pages=len(writer.pages),
                    sparse_native=True,padding=args.upload_profile=='standard-evaluation',dense_content_qualified=False)
                report['browser_pdf_sha256']=hashlib.sha256(pdf_bytes).hexdigest()
                page.click('[data-view="sources"]');page.fill('#file-version','browser-pdf-1')
                page.set_input_files('#file',dict(name='browser-native.pdf',mimeType='application/pdf',buffer=pdf_bytes))
                with page.expect_response(lambda response:response.url.endswith('/v1/files') and response.request.method=='POST',timeout=60000) as uploaded:
                    page.click('#upload-file')
                upload_response=uploaded.value
                if upload_response.status!=200:
                    report['browser_upload_failure']=dict(status=upload_response.status,body=upload_response.json())
                assert upload_response.status==200,'Actual browser PDF upload failed'
                # Large request bodies can evict Chromium's inspector response cache.
                # Inspect the receipt consumed and rendered by the actual UI instead.
                page.wait_for_function("() => document.getElementById('ingestion-evidence').textContent.includes('document_id')",timeout=30000)
                pdf_id=json.loads(page.locator('#ingestion-evidence').inner_text())['document_id']
                page.wait_for_function("() => [...document.querySelectorAll('#documents .card')].some(card=>card.textContent.includes('browser-native.pdf') && card.textContent.includes('Validated index available'))",timeout=120000)
                page.locator('#documents .card').filter(has_text='browser-native.pdf').get_by_role('button',name='Inspect source & manifest').click()
                page.wait_for_function('(id) => document.getElementById("source-inspector").textContent.includes(id)',arg=pdf_id,timeout=30000)
                page.click('#apply-chat-scope');page.fill('#question','What is the maximum operating temperature of Motor-Q?')
                with page.expect_response(lambda response:response.url.endswith('/v1/chat') and response.request.method=='POST',timeout=60000) as retrieved:
                    page.click('#send')
                evidence=retrieved.value.json()
                assert evidence['citations'] and all(citation['document_id']==pdf_id for citation in evidence['citations'])
                page.click('[data-view="memory"]')
                with page.expect_response(lambda response:'/v1/memory/' in response.url,timeout=30000) as refreshed:
                    page.click('#refresh-memory')
                memory_response=refreshed.value
                assert memory_response.status==200 and memory_response.json()['source_scope']['document_ids']==[pdf_id]
                assert memory_response.json()['source_scope']['revision']=='browser-pdf-1'
                report['browser_memory_scope_preserved']=True
                page.click('[data-view="chat"]')
                page.locator('#feed .assistant .citation').last.click()
                page.wait_for_function("() => document.getElementById('pdf-status').textContent.includes('Unique native text match highlighted')",timeout=60000)
                assert page.locator('#pdf-zoom').input_value()=='1','PDF zoom selector must match the reset render scale'
                rectangle=page.locator('#pdf-quote-layer .pdf-quote-mark').first.evaluate('(mark)=>({left:parseFloat(mark.style.left),top:parseFloat(mark.style.top),width:parseFloat(mark.style.width),height:parseFloat(mark.style.height)})')
                assert abs(rectangle['left']-60)<3 and 40<rectangle['top']<70 and rectangle['width']>100 and rectangle['height']>5
                page.select_option('#pdf-zoom','1.5')
                page.wait_for_function("() => parseFloat(document.querySelector('#pdf-quote-layer .pdf-quote-mark')?.style.left)>88",timeout=30000)
                page.screenshot(path=str(folder/'grounded-pdf-browser.png'),full_page=True)
                with page.expect_download() as downloading:page.click('#download-source')
                downloaded=temporary/'browser-downloaded-original.pdf';downloading.value.save_as(downloaded)
                assert hashlib.sha256(downloaded.read_bytes()).hexdigest()==report['browser_pdf_sha256']
                if args.upload_profile=='standard-evaluation':
                    page.fill('#pdf-page','250');page.click('#pdf-go')
                    page.wait_for_function("() => document.getElementById('pdf-status').textContent.includes('page 250/250')",timeout=30000)
                    page.select_option('#chat-scope','page')
                    page.fill('#question','What is the maximum operating temperature of Motor-Envelope?')
                    with page.expect_response(lambda response:response.url.endswith('/v1/chat'),timeout=30000) as tail_evidence:page.click('#send')
                    tail_result=tail_evidence.value.json()
                    assert tail_evidence.value.status==200 and tail_evidence.value.request.post_data_json['pages']==[250]
                    assert tail_result['citations'] and all(c['document_id']==pdf_id and c['anchor']['page']==250 for c in tail_result['citations'])
                    page.locator('#feed .assistant .citation').last.click()
                    page.wait_for_function("() => document.getElementById('pdf-status').textContent.includes('page 250/250') && document.getElementById('pdf-status').textContent.includes('Unique native text match highlighted')",timeout=60000)
                    with page.expect_response(lambda response:'/v1/memory/' in response.url,timeout=30000) as tail_memory:
                        page.click('[data-view="memory"]');page.click('#refresh-memory')
                    assert tail_memory.value.status==200 and tail_memory.value.json()['source_scope']['pages']==[250]
                    page.click('[data-view="chat"]');page.select_option('#chat-scope','document')
                    report['standard_upload_envelope']=dict(exact_25_mib=True,pages=250,tail_page_retrieval=True,
                        tail_page_native_highlight=True,memory_page_scope=True,download_sha256_exact=True,
                        dense_content_qualified=False,ocr_250_pages_qualified=False)
                report['pdf_browser']=dict(status='PASS_SCOPED',real_upload=True,real_parser=True,automatic_publication=True,
                    real_library_retrieval=True,unique_native_quote=True,geometry_100_percent=rectangle,
                    zoom_150_percent=True,download_matches_original=True,ocr_qualified=False)
                page.click('#browse-knowledge')
                page.wait_for_function("() => document.querySelectorAll('#knowledge-items .card').length>0",timeout=30000)
                page.select_option('#knowledge-kind','formula')
                with page.expect_response(lambda response:'/browse?' in response.url and 'kind=formula' in response.url,timeout=30000) as formulas:page.click('#knowledge-filter')
                assert formulas.value.status==200 and formulas.value.json()['items']
                assert formulas.value.json()['summary']['formula_detection_exhaustive'] is False
                with page.expect_response(lambda response:'/nodes/' in response.url,timeout=30000) as formula_node:
                    page.locator('#knowledge-items .card').first.get_by_role('button',name='Inspect node and relationships').click()
                formula_detail=formula_node.value.json()
                assert formula_detail['node']['kind']=='formula' and formula_detail['node']['formula_data']['evaluation']=='not_attempted'
                assert formula_detail['authority_granted'] is False and formula_detail['citation']['original_sha256']==report['browser_pdf_sha256']
                page.wait_for_function("() => document.getElementById('knowledge-detail').textContent.includes('formula_data')",timeout=30000)
                page.screenshot(path=str(folder/'grounded-knowledge-browser.png'),full_page=True)
                with page.expect_response(lambda response:'/nodes/' in response.url,timeout=30000) as neighboring:
                    page.locator('#knowledge-relationships .card').filter(has_text='derived from span').get_by_role('button',name='Explore neighboring node').click()
                assert neighboring.value.json()['node']['kind']=='source_span'
                page.get_by_role('button',name='Inspect original source',exact=True).click()
                page.wait_for_function("() => document.getElementById('pdf-status').textContent.includes('Unique native text match highlighted')",timeout=60000)
                report['knowledge_browser']=dict(status='PASS_SCOPED',real_authorized_graph=True,literal_kind_filter=True,
                    formula_lineage=True,evaluation_not_attempted=True,paged_relationship_navigation=True,
                    neighboring_source_span=True,exact_original_quote_navigation=True,authority_granted=False)
                with page.expect_response(lambda response:response.url.endswith('/v1/issues/analyze'),timeout=30000) as assembled:
                    page.click('#assemble-source')
                issue=assembled.value.json()
                assert assembled.value.status==200 and issue['state']=='candidate' and issue['authority_granted'] is False
                issue_id=issue['id']
                page.click('[data-view="review"]')
                import re
                page.locator('#claims .card').filter(has_text=re.compile('motor-q',re.I)).get_by_role('button',name='Use for learning').click()
                page.fill('#reflection','Compare this candidate claim with its original source before proposing an explanation.')
                with page.expect_response(lambda response:response.url.endswith('/v1/learning') and response.request.method=='POST',timeout=30000) as proposed:
                    page.click('#propose-learning')
                reflection=proposed.value.json()
                assert proposed.value.status==200 and reflection['state']=='candidate' and reflection['authority_granted'] is False
                page.click('#disconnect')
                assert page.locator('#identity').inner_text()=='Disconnected'
                assert page.locator('#feed').inner_text()=='' and page.locator('#token').input_value()==''
                assert page.locator('#source-inspector').inner_text()==''
                assert page.evaluate('() => localStorage.length===0 && sessionStorage.length===0')
                login('reviewer');page.click('[data-view="governed"]');page.click('#load-governed')
                record=page.locator('#governed-records .card').filter(has_text=issue_id)
                assert record.get_by_role('button',name='Review candidate',exact=True).is_disabled()
                record.get_by_role('button',name='Inspect source-bound payload').click()
                page.wait_for_function('(digest) => document.getElementById("governed-detail").textContent.includes(digest)',arg=report['browser_pdf_sha256'],timeout=30000)
                page.fill('#governed-rationale','Synthetic reviewer checked the exact source binding; this grants no factual or execution authority.')
                with page.expect_response(lambda response:'/v1/governed/records/' in response.url and response.url.endswith('/review'),timeout=30000) as reviewed:
                    page.locator('#governed-records .card').filter(has_text=issue_id).get_by_role('button',name='Review candidate',exact=True).click()
                assert reviewed.value.status==200 and reviewed.value.json()['authority_granted'] is False
                page.click('[data-view="memory"]');page.click('#load-learning')
                with page.expect_response(lambda response:'/v1/learning/' in response.url and response.url.endswith('/review'),timeout=30000) as learned:
                    page.locator('#learning-queue .card').filter(has_text=reflection['id']).get_by_role('button',name='Review reflection').click()
                assert learned.value.status==200 and learned.value.json()['authority_granted'] is False
                page.click('[data-view="governance"]')
                with page.expect_response(lambda response:response.url.endswith('/v1/audit'),timeout=30000) as audited:page.click('#load-audit')
                assert audited.value.status==200 and audited.value.json()['visible_row_hashes_valid'] is True
                page.click('#disconnect');login('admin');page.click('[data-view="governance"]');page.click('#load-policy')
                page.wait_for_function("() => document.getElementById('policy-data').textContent.includes('daily_call_limit')",timeout=30000)
                limit=int(page.input_value('#daily-limit'));page.fill('#daily-limit',str(limit+1))
                with page.expect_response(lambda response:response.url.endswith('/v1/admin/policy') and response.request.method=='PUT',timeout=30000) as staged:page.click('#save-policy')
                action=staged.value.json()
                assert staged.value.status==200 and action['state']=='pending-independent-review' and action['policy_unchanged']
                page.wait_for_function('(limit) => Number(document.getElementById("daily-limit").value)===limit',arg=limit,timeout=30000)
                page.click('[data-view="governed"]');page.click('#load-actions')
                assert page.locator('#policy-actions .card').filter(has_text=action['action_id']).get_by_role('button',name='Approve independent action',exact=True).is_disabled()
                page.click('#disconnect');login('reviewer');page.click('[data-view="governed"]');page.click('#load-actions')
                with page.expect_response(lambda response:'/v1/admin/actions/' in response.url and response.url.endswith('/review'),timeout=30000) as applied:
                    page.locator('#policy-actions .card').filter(has_text=action['action_id']).get_by_role('button',name='Approve independent action',exact=True).click()
                assert applied.value.status==200 and applied.value.json()['state']=='applied'
                page.click('#disconnect');login('viewer')
                assert page.locator('#send').is_disabled() and page.locator('#model').is_disabled()
                denied=page.evaluate("async () => (await fetch('/v1/chat',{method:'POST',headers:{'Authorization':'Bearer '+token,'Content-Type':'application/json'},body:JSON.stringify({question:'Motor-Q temperature?'})})).status")
                assert denied==403
                page.click('#disconnect')
                report['governed_browser']=dict(status='PASS_SCOPED',source_bound_issue=True,inspected_payload_required=True,
                    synthetic_reviewer_role=True,review_grants_no_factual_authority=True,learning_review=True,
                    scoped_audit_rows_valid=True,sensitive_policy_staged=True,self_approval_disabled=True,
                    second_role_applies_action=True,viewer_chat_denied_by_server=True,independent_human_acceptance=False)
                login('operator');page.click('[data-view="sources"]')
                ocr_bytes=(ocr_fixture/'original-raster.pdf').read_bytes()
                assert hashlib.sha256(ocr_bytes).hexdigest()==ocr_manifest['pdf_sha256']
                page.fill('#file-version','browser-ocr-1')
                page.set_input_files('#file',dict(name='browser-ocr.pdf',mimeType='application/pdf',buffer=ocr_bytes))
                with page.expect_response(lambda response:response.url.endswith('/v1/files') and response.request.method=='POST',timeout=150000) as ocr_upload:page.click('#upload-file')
                assert ocr_upload.value.status==200,'Actual browser OCR upload failed'
                ocr_id=ocr_upload.value.json()['document_id']
                page.wait_for_function("() => [...document.querySelectorAll('#documents .card')].some(card=>card.textContent.includes('browser-ocr.pdf') && card.textContent.includes('Validated index available'))",timeout=120000)
                page.locator('#documents .card').filter(has_text='browser-ocr.pdf').get_by_role('button',name='Inspect source & manifest').click()
                page.wait_for_function('(id) => document.getElementById("source-inspector").textContent.includes(id)',arg=ocr_id,timeout=30000)
                archived=page.evaluate("async id => (await (await fetch('/v1/sources/'+id,{headers:{Authorization:'Bearer '+token}})).json()).manifest.documents[0].metadata.extraction_history",ocr_id)
                assert len(archived)==1 and archived[0]['kind']=='native-before-ocr'
                assert archived[0]['payload']['original_sha256']==hashlib.sha256(ocr_bytes).hexdigest()
                assert archived[0]['payload']['page_count']==4 and all(record['status']=='ocr_required' for record in archived[0]['payload']['pages'])
                page.click('#open-pdf')
                page.wait_for_function("() => document.getElementById('pdf-canvas').width>0",timeout=60000)
                page.select_option('#chat-scope','page');page.fill('#question','What words occur near Pump and Valve?')
                with page.expect_response(lambda response:response.url.endswith('/v1/chat'),timeout=30000) as ocr_evidence:page.click('#send')
                ocr_answer=ocr_evidence.value.json();ocr_scope=ocr_evidence.value.request.post_data_json
                assert ocr_scope['document_ids']==[ocr_id] and ocr_scope['pages']==[1]
                assert ocr_answer['citations'] and all(citation['document_id']==ocr_id and citation['anchor']['page']==1 for citation in ocr_answer['citations'])
                page.locator('#feed .assistant .citation').last.click()
                page.wait_for_function("() => document.getElementById('pdf-status').textContent.includes('Unique OCR word regions highlighted')",timeout=60000)
                assert page.locator('#pdf-text-layer').inner_text()==''
                marks=page.locator('#pdf-quote-layer .pdf-quote-mark');assert marks.count()>=4
                first_mark=marks.first.evaluate('(mark)=>({left:parseFloat(mark.style.left),top:parseFloat(mark.style.top)})')
                oracle=ocr_manifest['labels'][0]['ink_box']
                assert abs(first_mark['left']-oracle[0]*72/300)<1 and abs(first_mark['top']-oracle[1]*72/300)<1
                painted=marks.first.evaluate('''mark=>{
                    const c=document.getElementById('pdf-canvas'),x=c.width/c.clientWidth,y=c.height/c.clientHeight;
                    const p=c.getContext('2d').getImageData(Math.floor(parseFloat(mark.style.left)*x),Math.floor(parseFloat(mark.style.top)*y),Math.ceil(parseFloat(mark.style.width)*x),Math.ceil(parseFloat(mark.style.height)*y)).data;
                    let ink=0;for(let i=0;i<p.length;i+=4)if(p[i]<160)ink++;return {ink,scaleX:x,scaleY:y};
                }''')
                assert painted['ink']>15 and abs(painted['scaleX']-args.browser_dpr)<.01 and abs(painted['scaleY']-args.browser_dpr)<.01
                page.screenshot(path=str(folder/'grounded-ocr-browser.png'),full_page=True)
                report['ocr_browser']=dict(status='PASS_SCOPED',real_ocr_service=True,real_upload_and_publication=True,
                    exact_page_scope=True,page_local_unique_word_regions=True,native_text_absent=True,
                    independent_ink_position_oracle=True,first_region=first_mark,painted_raster=painted,
                    complete_pre_ocr_native_representation_retained=True,recognition_verified=False,
                    limitations=['synthetic English raster PDF','identity 300 DPI; no rotation/crop/multilingual acceptance'])
                if ocr_manifest.get('schema')=='nsai.ocr-right-angle-oracle/1':
                    checked=[dict(page=1,rotation=0,first_region=first_mark)]
                    for case in ocr_manifest['cases'][1:]:
                        number=case['page']
                        page.fill('#pdf-page',str(number));page.click('#pdf-go')
                        page.wait_for_function('(number) => document.getElementById("pdf-status").textContent.includes(`page ${number}/4`)',arg=number,timeout=30000)
                        page.click('#apply-chat-scope');page.fill('#question','What words occur near Pump and Valve?')
                        with page.expect_response(lambda response:response.url.endswith('/v1/chat'),timeout=30000) as rotated_evidence:page.click('#send')
                        result=rotated_evidence.value.json()
                        assert rotated_evidence.value.status==200 and rotated_evidence.value.request.post_data_json['pages']==[number]
                        assert result['citations'] and all(c['anchor']['page']==number and c['document_id']==ocr_id for c in result['citations'])
                        page.locator('#feed .assistant .citation').last.click()
                        page.wait_for_function('(number) => document.getElementById("pdf-status").textContent.includes(`page ${number}/4`) && document.getElementById("pdf-status").textContent.includes("Unique OCR word regions highlighted")',arg=number,timeout=60000)
                        mark=page.locator('#pdf-quote-layer .pdf-quote-mark').first.evaluate('(mark)=>({left:parseFloat(mark.style.left),top:parseFloat(mark.style.top)})')
                        assert abs(mark['left']-oracle[0]*.24)<3 and abs(mark['top']-oracle[1]*.24)<3
                        checked.append(dict(page=number,rotation=case['rotation'],first_region=mark))
                        if case['rotation']==90:
                            page.select_option('#pdf-zoom','1.5')
                            page.wait_for_function('(expected) => Math.abs(parseFloat(document.querySelector("#pdf-quote-layer .pdf-quote-mark")?.style.left)-expected)<2',arg=oracle[0]*.36,timeout=30000)
                            zoomed=page.locator('#pdf-quote-layer .pdf-quote-mark').first.evaluate('(mark)=>({left:parseFloat(mark.style.left),top:parseFloat(mark.style.top)})')
                            assert abs(zoomed['top']-oracle[1]*.36)<3
                            checked[-1]['zoom_150_percent']=zoomed
                            page.select_option('#pdf-zoom','1')
                            page.wait_for_function('(expected) => Math.abs(parseFloat(document.querySelector("#pdf-quote-layer .pdf-quote-mark")?.style.left)-expected)<2',arg=oracle[0]*.24,timeout=30000)
                        page.screenshot(path=str(folder/f'grounded-ocr-rotation-{case["rotation"]}.png'),full_page=True)
                    report['ocr_browser'].update(right_angle_crop_cases=checked,independent_ink_position_oracle=True,
                        limitations=['synthetic upright English raster at 300 DPI under intrinsic right-angle rotations and offset crops',
                            'No arbitrary skew, UserUnit, sideways-text recognition, multilingual or general OCR accuracy acceptance'])
                page.click('#disconnect')
                private_requests=[]
                def private_request(request):
                    if '/v1/' in request.url:private_requests.append(request.url.split('/v1/',1)[1])
                page.on('request',private_request)
                page.fill('#token',(temporary/'private-user').read_text(encoding='utf-8'));page.click('#connect')
                page.wait_for_function("() => document.getElementById('notice').textContent.includes('Authenticated. Private document access awaits')",timeout=30000)
                page.wait_for_function("() => !document.getElementById('connect').disabled",timeout=30000)
                assert page.locator('#identity').inner_text().startswith('operator')
                assert 'local-user-browser' in page.locator('#identity').inner_text()
                assert page.locator('#send').is_disabled() and page.locator('#upload').is_disabled() and page.locator('#model').is_disabled()
                assert page.locator('#library-search').is_disabled() and page.locator('#documents .card').count()==0
                assert set(private_requests)=={'capabilities','model/status'}
                denied=page.evaluate("async () => (await fetch('/v1/documents',{headers:{Authorization:'Bearer '+token}})).status")
                assert denied==503
                report['withheld_private_login']=dict(status='PASS_SCOPED',real_registry=True,authenticated=True,
                    only_status_requests_automatically=True,content_controls_disabled=True,server_gate_remains_closed=True)
                page.click('#disconnect')
                assert not errors and not external
                report['browser']=dict(status='PASS_SCOPED',real_api=True,api_interception=False,
                    device_pixel_ratio=args.browser_dpr,
                    source_revision_scope=True,actual_cpu_model_answer=True,source_hash_inspection=True,
                    private_canary_absent=True,logout_clears_workspace=True,no_browser_storage=True,
                    page_errors=errors,external_requests=external,individual_private_http_qualified=False)
                context.close();browser.close()
            report['status']='PASS_SCOPED'
    except Exception as error:
        report['failure_type']=type(error).__name__;report['failure']=str(error)[:500]
        report['failure_stack']=traceback.format_exc()
    finally:
        for component in ('parser_server','ocr_server','model','encoder'):
            name=locals().get(component)
            if name and name in stack.containers:
                output=command(['logs',name],ok=False)
                (folder/(component+'-output.txt')).write_bytes(output.stdout)
                (folder/(component+'-errors.txt')).write_bytes(output.stderr)
                if component=='model':
                    statistics=command(['exec',name,'cat','/sys/fs/cgroup/cpu.stat'],ok=False)
                    (folder/'model-cpu-stat.txt').write_bytes(statistics.stdout)
        if 'api_server' in locals() and api_server in stack.containers:
            output=command(['logs',api_server],ok=False)
            (folder/'api-output.txt').write_bytes(output.stdout);(folder/'api-errors.txt').write_bytes(output.stderr)
        if 'client' in locals() and client in stack.containers and not (folder/'worker-output.json').exists():
            output=command(['logs',client],ok=False)
            (folder/'worker-output.json').write_bytes(output.stdout);(folder/'worker-errors.txt').write_bytes(output.stderr)
        report['source_after']=source_snapshot(ROOT);report['fixture_after']=hashes()
        if report['source_before']!=report['source_after'] or report['fixture_before']!=report['fixture_after']:report['status']='FAIL'
        stack.cleanup();report['cleanup_complete']=stack.receipt['cleanup_complete']
        if model_volume:
            metadata=json.loads(command(['volume','inspect',model_volume]).stdout)[0]
            assert metadata['Labels'].get('nsai.owner')==stack.tag
            report['model_volume_removed']=command(['volume','rm',model_volume],ok=False).returncode==0
            report['cleanup_complete']=report['cleanup_complete'] and report['model_volume_removed']
        if not report['cleanup_complete']:report['status']='FAIL'
        report['artifact_sha256']={path.name:hashlib.sha256(path.read_bytes()).hexdigest() for path in folder.iterdir() if path.is_file() and path.name!='grounded-receipt.json'}
        (folder/'grounded-receipt.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=report['status'],run_id=owner,cleanup=report['cleanup_complete'])))
    return 0 if report['status']=='PASS_SCOPED' else 1


if __name__=='__main__':raise SystemExit(main())
