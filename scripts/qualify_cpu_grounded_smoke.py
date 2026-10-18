"""Owned CPU generation through application admission and citation validation.

Two synthetic source questions are smoke checks, not held-out answer-quality,
full HTTP/private access, licensing or release acceptance. Never reads live config.
"""
import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import tempfile
import time
from uuid import uuid4

ROOT=Path(__file__).resolve().parent.parent
LLAMA='sha256:89f180f16f295ee496fe00924ec2118cae2efec519d1a82c605420af09d2a6df'
REVISION='91cad51170dc346986eccefdc2dd33a9da36ead9'
MODEL_SHA='6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e'


async def worker():
    import httpx
    from nsai import inference
    key=Path('/run/token').read_text().strip()
    async with httpx.AsyncClient(trust_env=False,timeout=3) as client:
        for _ in range(120):
            try:
                response=await client.get('http://llama-cpp:8080/health',headers={'Authorization':'Bearer '+key})
                if response.status_code==200:break
            except httpx.HTTPError:pass
            await asyncio.sleep(.5)
        else:raise RuntimeError('Owned model readiness deadline exceeded')
    records=[]
    for width in (32,64):
        hit=dict(id='a'*width,document_id='b'*32,title='Synthetic motor manual',revision='1',
                 locator='line:1',original_sha256='c'*64,media_type='text/plain',
                 text='Motor-X maximum operating temperature is 75 C.',projection_status='candidate')
        question='What is the maximum operating temperature of Motor-X?'
        prepared=inference.prepare_source_request(question,[hit],max_tokens=256)
        admission=await inference.admit_source_request(prepared)
        result=await inference.generate_from_sources(question,[hit],max_tokens=256,prepared=prepared,admission=admission)
        passed=(result['mode']=='model_unverified' and result['citation_validation']=='references-resolve'
                and '75' in result['answer'] and result['answer_verified'] is False
                and len(result['citations'])==1 and result['citations'][0]['chunk_id']==hit['id'])
        records.append(dict(citation_id_width=width,pass_=passed,result=result))
    print(json.dumps(dict(records=records,all_pass=all(record['pass_'] for record in records))))


def main():
    from check_release_readiness import source_snapshot
    from prepare_cpu_model import verify_model
    owner=uuid4().hex;prefix='nsai-grounded-'+owner[:12];network=prefix+'-net'
    folder=ROOT/'evidence/cpu-grounded-smoke'/owner;folder.mkdir(parents=True)
    model_path=ROOT/'state/models/qwen2.5-1.5b-instruct-evaluation'/REVISION/'qwen2.5-1.5b-instruct-q4_k_m.gguf'
    report=dict(status='FAIL',run_id=owner,scope=__doc__,host_ports=False,live_services_accessed=False,
                source_before=source_snapshot(ROOT),cleanup=[],model=verify_model(model_path,MODEL_SHA))
    containers=[];made_network=False;key=secrets.token_hex(32)
    def command(arguments,*,timeout=60,ok=True):
        result=subprocess.run(['docker',*arguments],capture_output=True,timeout=timeout)
        if ok and result.returncode:raise RuntimeError('Owned CPU qualification command failed')
        return result
    def cleanup(kind,name):
        found=command(([kind,'inspect',name] if kind=='network' else ['inspect',name]),ok=False)
        if found.returncode:return True
        item=json.loads(found.stdout)[0]
        labels=item.get('Labels',{}) if kind=='network' else item['Config'].get('Labels',{})
        if labels.get('nsai.owner')!=owner:raise RuntimeError('Unowned CPU cleanup refused')
        return command(['network','rm',name] if kind=='network' else ['rm','--force',name],ok=False).returncode==0
    try:
        application=command(['image','inspect','nsai-implementation-candidate:local','--format','{{.Id}}']).stdout.decode().strip()
        command(['image','inspect',LLAMA]);report['images']=dict(model=LLAMA,application=application)
        command(['network','create','--internal','--label','nsai.owner='+owner,network]);made_network=True
        with tempfile.TemporaryDirectory(prefix=prefix) as temporary:
            token=Path(temporary)/'token';token.write_text(key)
            common=['--label','nsai.owner='+owner,'--network',network,'--read-only','--cap-drop','ALL',
                    '--security-opt','no-new-privileges:true','--pids-limit','128','--user','10001:10001',
                    '--tmpfs','/tmp:rw,nosuid,nodev,noexec,size=64m,mode=1777',
                    '--mount','type=bind,source='+str(token)+',target=/run/token,readonly']
            model_name=prefix+'-model';containers.append(model_name)
            command(['run','-d','--name',model_name,*common,'--network-alias','llama-cpp','--cpus','2','--memory','4g',
                '--mount','type=bind,source='+str(model_path)+',target=/models/model.gguf,readonly',LLAMA,
                '-m','/models/model.gguf','--alias','nsai-local-qwen','--host','0.0.0.0','--port','8080',
                '--ctx-size','4096','--parallel','1','--threads','2','--n-gpu-layers','0',
                '--no-ui','--no-agent','--no-slots','--api-key-file','/run/token','--timeout','125'])
            name=prefix+'-client';containers.append(name)
            command(['run','-d','--name',name,*common,'--cpus','1','--memory','512m',
                '--mount','type=bind,source='+str(Path(__file__).resolve())+',target=/qualification.py,readonly',
                '-e','NSAI_MODEL_URL=http://llama-cpp:8080/v1','-e','NSAI_MODEL_NAME=nsai-local-qwen',
                '-e','NSAI_MODEL_PROVIDER=owned-cpu-evaluation','-e','NSAI_MODEL_API_KEY_FILE=/run/token',
                '--entrypoint','python',application,'/qualification.py','--worker'])
            exited=command(['wait',name],timeout=360).stdout.decode().strip()
            logs=command(['logs',name]);output=logs.stdout.decode('utf-8')
            diagnostics=logs.stderr.decode('utf-8',errors='replace').replace(key,'[owned credential]')
            (folder/'stderr.txt').write_text(diagnostics,encoding='utf-8')
            if exited!='0':raise RuntimeError('Owned CPU worker failed; diagnostics retained')
            result=json.loads(output);report['result']=result
            report['status']='PASS_SCOPED' if result['all_pass'] else 'QUALITY_FAILED'
    except Exception as error:report['failure_type']=type(error).__name__;report['failure']=str(error)[:500]
    finally:
        for name in reversed(containers):report['cleanup'].append(dict(resource=name,removed=cleanup('container',name)))
        if made_network:report['cleanup'].append(dict(resource=network,removed=cleanup('network',network)))
        report['source_after']=source_snapshot(ROOT)
        report['sources_unchanged']=report['source_before']==report['source_after']
        report['owned_resources_removed']=all(item['removed'] for item in report['cleanup'])
        if not report['sources_unchanged'] or not report['owned_resources_removed']:report['status']='FAIL'
        (folder/'receipt.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=report['status'],run_id=owner,cleanup=report['owned_resources_removed'])))
    return 0 if report['status']=='PASS_SCOPED' else 1


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--worker',action='store_true');arguments=parser.parse_args()
    if arguments.worker:asyncio.run(worker())
    else:raise SystemExit(main())
