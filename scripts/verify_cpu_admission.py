"""Read-only tokenizer admission and one CPU generation, without application DB.

Host mode starts an owned candidate container on the existing private model-only
network, mounting current source and the model token read-only. No API/database
credentials, source uploads, budget reservations or application writes occur.
"""
from __future__ import annotations
import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

async def inside():
    import httpx
    from nsai import inference
    base,model,key=inference.model_settings()
    headers={'Authorization':'Bearer '+key}
    async with httpx.AsyncClient(timeout=10,trust_env=False,follow_redirects=False) as client:
        props=await inference._bounded_json(client,'GET',base[:-3]+'/props',headers=headers)
    actual_context=props['default_generation_settings']['n_ctx']
    configured=int(os.environ['NSAI_MODEL_CONTEXT_TOKENS'])
    hit=dict(id='a'*32,document_id='b'*32,revision=1,projection_status='candidate',locator='line:1',
        text='Pump-X maximum operating temperature is 75 C.',title='Independent synthetic admission fixture',original_sha256=hashlib.sha256(b'Pump-X maximum operating temperature is 75 C.').hexdigest())
    question='What is the maximum temperature? Answer briefly from the source.'
    body=inference.prepare_source_request(question,[hit],max_tokens=50)
    admitted=await inference.admit_source_request(body)
    overflow_hits=[dict(hit,id=f'{index:032x}',text='a '*600) for index in range(12)]
    overflow=inference.prepare_source_request('Summarize source limits.',overflow_hits,max_tokens=50)
    overflow_context='\n'.join(f"[{h['id']}] rev={h['revision']} projection={h['projection_status']} {h['locator']}: {h['text'][:1200]}" for h in overflow_hits)
    overflow_refused=False;overflow_error=None
    try:await inference.admit_source_request(overflow)
    except ValueError as error:overflow_refused=True;overflow_error=str(error)
    # Read-only native routes count the exact complete templated overflow payload;
    # no overflowing generation request is sent to the provider.
    async with httpx.AsyncClient(timeout=10,trust_env=False,follow_redirects=False) as client:
        template=await inference._bounded_json(client,'POST',base[:-3]+'/apply-template',headers=headers,payload={'messages':overflow['messages']})
        tokenized=await inference._bounded_json(client,'POST',base[:-3]+'/tokenize',headers=headers,
            payload={'content':template['prompt']+'\n'+json.dumps(overflow['response_format'],ensure_ascii=False),'add_special':True,'parse_special':True})
    overflow_tokens=len(tokenized['tokens'])
    medium_hits=[dict(hit,id=f'{index:032x}',text='a '*400) for index in range(12)]
    medium=inference.prepare_source_request('Summarize source limits.',medium_hits,max_tokens=50)
    medium_admission=None
    if configured>=8192:
        medium_admission=await inference.admit_source_request(medium)
    started=time.monotonic()
    generated=await inference.generate_from_sources(question,[hit],max_tokens=50,prepared=body,admission=admitted)
    elapsed=time.monotonic()-started
    cases=[dict(case='supported_complete_prompt_admitted',pass_=admitted['admitted'] and admitted['total_tokens']<=admitted['context_tokens']),
        dict(case='stricter_actual_or_configured_context',pass_=admitted['context_tokens']==min(actual_context,configured)),
        dict(case='overflow_passes_old_byte_guard',pass_=len(overflow_context.encode())<=20000),
        dict(case='overflow_complete_prompt_refused_before_generation',pass_=overflow_refused and overflow_tokens+50+64>min(actual_context,configured)),
        dict(case='generation_unverified',pass_=not generated['answer_verified'] and generated['mode'] in {'model_unverified','citation_guard_fallback'}),
        dict(case='source_bound_citation_or_safe_fallback',pass_=bool(generated['citations']) and all(c['chunk_id']==hit['id'] and c['original_sha256']==hit['original_sha256'] for c in generated['citations']))]
    if configured>=8192:
        cases.append(dict(case='larger_than_4k_complete_prompt_admitted_without_generation',pass_=4096<medium_admission['total_tokens']<=8192))
    import platform
    result=dict(cases=cases,all_pass=all(c['pass_'] for c in cases),actual_server_context_tokens=actual_context,
        configured_admission_context_tokens=configured,supported_admission=admitted,medium_admission=medium_admission,
        overflow=dict(context_utf8_bytes=len(overflow_context.encode()),old_byte_guard_limit=20000,prompt_tokens=overflow_tokens,
            reserved_output_tokens=50,safety_tokens=64,total_tokens=overflow_tokens+114,refused=overflow_refused,reason=overflow_error,
            generation_calls=0,historical_reference='Original audit context-alone4632tokens before schema/system/output; new deterministic payload counts above are independent'),
        generation=dict(calls=1,seconds=elapsed,max_tokens=50,usage=generated.get('usage'),mode=generated['mode'],
            answer=generated['answer'],answer_verified=False,citation_validation=generated['citation_validation'],support_validation=generated['support_validation']),
        runtime=dict(python=platform.python_version(),machine=platform.machine()),
        isolation='No application API/DB access, reservations, budget state or uploads; one ordinary private-model generation only',
        qualification_scope='Tokenizer/admission and one source-bound generation smoke check; not model quality/latency SLO qualification')
    print(json.dumps(result,ensure_ascii=False))
    return 0 if result['all_pass'] else 1

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--context-tokens',type=int,choices=[4096,8192],default=4096);parser.add_argument('--inside',action='store_true');parser.add_argument('--output',type=Path,default=Path('evidence/implementation/model-runtime-admission.json'));args=parser.parse_args()
    if args.inside:raise SystemExit(asyncio.run(inside()))
    root=Path(__file__).resolve().parents[1];image='nsai-implementation-candidate:local'
    pinned_image=json.loads(subprocess.run(['docker','image','inspect',image],capture_output=True,text=True,check=True).stdout)[0]['Id']
    before_hashes={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'src/nsai').rglob('*.py')}
    command=['docker','run','--rm','--name','nsai-model-admission-'+str(os.getpid()),'--label','nsai.scope=owned-model-qualification',
        '--network','amd-hackathon-nsai_model_net','--read-only','--user','10001:10001','--cap-drop','ALL','--security-opt','no-new-privileges:true',
        '--cpus','1','--memory','384m','--pids-limit','32','--tmpfs','/tmp:rw,noexec,nosuid,size=32m',
        '--mount',f'type=bind,source={root / "src"},target=/qualified-src,readonly',
        '--mount',f'type=bind,source={Path(__file__).resolve()},target=/verify.py,readonly',
        '--mount',f'type=bind,source={root / "secrets/model_token.txt"},target=/run/secrets/model_token,readonly',
        '--env','PYTHONPATH=/qualified-src','--env','NSAI_MODEL_URL=http://llama-cpp:8080/v1','--env','NSAI_MODEL_NAME=nsai-local-qwen',
        '--env','NSAI_MODEL_PROVIDER=local-llamacpp-cpu','--env','NSAI_MODEL_API_KEY_FILE=/run/secrets/model_token',
        '--env','NSAI_MODEL_CONTEXT_TOKENS='+str(args.context_tokens),'--entrypoint','python',pinned_image,'/verify.py','--inside']
    run=subprocess.run(command,capture_output=True,text=True,timeout=155)
    result=json.loads(run.stdout)
    import datetime
    result.update(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),exit_code=run.returncode,
        candidate_image_id=pinned_image,
        source_binding='Current source bound read-only at/qualified-src overrides immutablecandidate Python package; distinct from liveAPI image',
        source_hashes={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'src/nsai').rglob('*.py')},
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    result['source_hashes_before']=before_hashes
    result['source_unchanged_during_run']=before_hashes==result['source_hashes']
    if not result['source_unchanged_during_run']:
        result['all_pass']=False
        result['binding_limit']='Concurrent source mutation detected; behavior receipt retained but qualification not accepted'
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(dict(exit_code=run.returncode,all_pass=result['all_pass'],generation_mode=result['generation']['mode'],overflow_tokens=result['overflow']['prompt_tokens'],actual_context=result['actual_server_context_tokens'],seconds=result['generation']['seconds'])))
    raise SystemExit(0 if run.returncode==0 and result['all_pass'] else 1)

if __name__=='__main__':main()
