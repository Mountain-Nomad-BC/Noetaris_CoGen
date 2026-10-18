"""Bounded synthetic CPU experiment; never selects the production model endpoint."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import time
import urllib.request
from uuid import uuid4

ROOT=Path(__file__).resolve().parent.parent
LLAMA='sha256:89f180f16f295ee496fe00924ec2118cae2efec519d1a82c605420af09d2a6df'
PROFILE=dict(short_samples=30,long_admission_samples=30,short_max_output=32,long_max_output=50,
    context_profiles=[4096,8192],cpu=2,memory_bytes=4294967296,threads=2,parallel=1,
    whole_job_seconds=1200,financial_cost=None,verified_outcome_cost=None,
    scope='synthetic commissioned CPU experiment; no application or general quality/SLO certification')

def cmd(args,timeout=60):
    p=subprocess.run(args,capture_output=True,timeout=timeout)
    if p.returncode:raise RuntimeError('Owned Docker operation failed; driver output withheld')
    return p.stdout

def write(path,data):
    path.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def worker(cap):
    token=Path('/run/token').read_text().strip();end=float(os.environ['BENCH_END'])
    records=[];base='http://model:8080'
    def request(path,payload=None):
        if time.time()>=end:raise TimeoutError('Whole experiment deadline')
        data=None if payload is None else json.dumps(payload).encode()
        req=urllib.request.Request(base+path,data=data,headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=min(180,max(1,end-time.time()))) as r:
            raw=r.read(1048577)
            if len(raw)>1048576:raise ValueError('Oversized experiment response')
            return json.loads(raw)
    cold_start=time.monotonic()
    while True:
        try:
            request('/health');break
        except Exception:
            if time.time()>=end:raise TimeoutError('Model readiness deadline')
            time.sleep(1)
    readiness=time.monotonic()-cold_start
    def body(question,long=False):
        # A source citation and exact quantity are independent of model wording.
        filler=('Unrelated maintenance log: inspection completed without a recorded limit.\n'*850) if long else ''
        source=filler[:len(filler)//2]+'\n[SRC-75] Pump-X operating limit is 75 C.\n'+filler[len(filler)//2:]
        return dict(model='nsai-local-qwen',temperature=0,seed=42,max_tokens=50 if long else 32,stream=False,
            messages=[dict(role='system',content='Use only the source. Reply exactly: 75 C [SRC-75].'),
            dict(role='user',content=source+'\nQuestion: '+question)])
    # Tune filler length by actual tokenizer once; all long cases reuse exact prompt.
    longbody=body('What is the Pump-X operating limit?',True)
    def count(payload):
        prompt=request('/apply-template',{'messages':payload['messages']})['prompt']
        return len(request('/tokenize',{'content':prompt,'add_special':True,'parse_special':True})['tokens'])
    initial=count(longbody)
    content=longbody['messages'][1]['content']
    # Reduce only filler, preserving source/needle and final question.
    if initial>6400:
        longbody=body('What is the Pump-X operating limit?',False)
        filler='Unrelated maintenance log: inspection completed.\n'
        n=1000
        while True:
            longbody['messages'][1]['content']=filler*n+'\n[SRC-75] Pump-X operating limit is 75 C.\n'+filler*n+'\nWhat is the Pump-X operating limit?'
            size=count(longbody)
            if 5800<=size<=6400:break
            n=max(1,int(n*6100/size))
    longtokens=count(longbody)
    if not 5800<=longtokens<=6400:raise ValueError('Long fixture outside declared approximately6K token window')
    for i in range(31):
        payload=body('What is the Pump-X operating limit?')
        started=time.perf_counter();result=request('/v1/chat/completions',payload);elapsed=(time.perf_counter()-started)*1000
        answer=result['choices'][0]['message']['content'];usage=result.get('usage',{})
        records.append(dict(kind='cold-first-generation' if i==0 else 'warm-short',index=i,latency_ms=elapsed,
            answer=answer,source_oracle_pass='75 C' in answer and '[SRC-75]' in answer,
            answer_verified=False,usage=usage))
        print(json.dumps({'progress':records[-1]}),flush=True)
    for i in range(30):
        start=time.perf_counter();tokens=count(longbody);total=tokens+50+64
        records.append(dict(kind='long-tokenizer-only',index=i,latency_ms=(time.perf_counter()-start)*1000,
            prompt_tokens=tokens,total_reserved_tokens=total,admitted=total<=cap,
            admission_expected=(cap==8192),generation_called=False))
        print(json.dumps({'progress':records[-1]}),flush=True)
    if cap==8192:
        start=time.perf_counter();result=request('/v1/chat/completions',longbody)
        answer=result['choices'][0]['message']['content']
        records.append(dict(kind='one-long-generation',latency_ms=(time.perf_counter()-start)*1000,
            answer=answer,source_oracle_pass='75 C' in answer and '[SRC-75]' in answer,
            answer_verified=False,usage=result.get('usage',{}),prompt_tokens=longtokens))
        print(json.dumps({'progress':records[-1]}),flush=True)
    warm=[r['latency_ms'] for r in records if r['kind']=='warm-short'];warm.sort()
    print(json.dumps(dict(result=dict(context=cap,readiness_ms=readiness*1000,records=records,
        warm_p50_ms=warm[math.ceil(len(warm)*.5)-1],warm_p95_ms=warm[math.ceil(len(warm)*.95)-1],
        all_oracles_pass=all(r.get('source_oracle_pass',True) and r.get('admitted',True)==r.get('admission_expected',True) for r in records)))),flush=True)

def main():
    tag='nsai-cpu-context-'+uuid4().hex[:12];out=ROOT/'evidence/implementation/cpu-context-benchmark';out.mkdir(parents=True,exist_ok=True)
    receipt=dict(run_id=tag,status='RUNNING',profile=PROFILE,profiles=[],production_calls=False,
        source_sha256={Path(__file__).relative_to(ROOT).as_posix():hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    dest=out/(tag+'-receipt.json');write(out/'predeclared-profile.json',PROFILE);write(dest,receipt)
    network=tag+'-net';containers=[];deadline=time.time()+1200
    try:
        env={}
        for line in (ROOT/'.env').read_text().splitlines():
            if line.startswith(('NSAI_GGUF_PATH=','NSAI_GGUF_SHA256=')):
                k,v=line.split('=',1);env[k]=v.strip().strip('"')
        from prepare_cpu_model import verify_model
        model=verify_model(env['NSAI_GGUF_PATH'],env['NSAI_GGUF_SHA256'])
        receipt['model_sha256']=model['sha256'];receipt['model_bytes']=model['bytes']
        cmd(['docker','image','inspect',LLAMA]);client=json.loads(cmd(['docker','image','inspect','nsai-implementation-candidate:local']))[0]['Id']
        receipt.update(model_image=LLAMA,client_image=client)
        cmd(['docker','network','create','--internal','--label','nsai.owner='+tag,network])
        with tempfile.TemporaryDirectory(prefix='nsai-owned-cpu-') as tmp:
            # llama.cpp consumes this file literally; clients must use identical bytes.
            token=Path(tmp)/'token';token.write_text(secrets.token_hex(32))
            common=['--label','nsai.owner='+tag,'--network',network,'--read-only','--cap-drop','ALL','--security-opt','no-new-privileges:true','--pids-limit','128','--user','10001:10001','--tmpfs','/tmp:rw,nosuid,nodev,noexec,size=64m,mode=1777']
            for cap in [4096,8192]:
                if time.time()>=deadline:raise TimeoutError('Whole experiment deadline')
                name=tag+'-'+str(cap);containers.append(name)
                cmd(['docker','run','-d','--name',name,*common,'--network-alias','model','--cpus','2','--memory','4g',
                    '--mount',f'type=bind,source={env["NSAI_GGUF_PATH"]},target=/models/model.gguf,readonly',
                    '--mount',f'type=bind,source={token},target=/run/token,readonly',LLAMA,
                    '-m','/models/model.gguf','--alias','nsai-local-qwen','--host','0.0.0.0','--port','8080',
                    '--ctx-size',str(cap),'--parallel','1','--threads','2','--n-gpu-layers','0','--no-ui','--no-agent','--no-slots','--api-key-file','/run/token','--timeout','180'])
                workername=name+'-client';containers.append(workername)
                args=['docker','run','--name',workername,*common,'--cpus','1','--memory','512m','--env','BENCH_END='+str(deadline),
                    '--mount',f'type=bind,source={Path(__file__).resolve()},target=/benchmark.py,readonly',
                    '--mount',f'type=bind,source={token},target=/run/token,readonly','--entrypoint','python',client,'/benchmark.py','--worker',str(cap)]
                rawpath=out/(tag+'-'+str(cap)+'-raw.jsonl')
                with rawpath.open('wb') as raw:
                    run=subprocess.run(args,stdout=raw,stderr=subprocess.DEVNULL,timeout=max(1,deadline-time.time()))
                resources=cmd(['docker','exec',name,'cat','/sys/fs/cgroup/memory.peak']).decode().strip()
                lines=[json.loads(x) for x in rawpath.read_text().splitlines() if x]
                results=[x['result'] for x in lines if 'result' in x]
                result=results[-1] if results else dict(context=cap,status='INCOMPLETE',partial_records=[x['progress'] for x in lines if 'progress'in x])
                result.update(exit_code=run.returncode,model_cgroup_memory_peak_bytes=int(resources),worker_errors=[x['worker_error'] for x in lines if 'worker_error'in x])
                receipt['profiles'].append(result);write(dest,receipt)
                cmd(['docker','rm','-f',workername,name]);containers.remove(workername);containers.remove(name)
                if run.returncode:raise RuntimeError('Owned experiment worker incomplete; retained partial samples')
        receipt['status']='PASS_SCOPED' if all(p.get('all_oracles_pass') for p in receipt['profiles']) else 'QUALITY_FAILED'
    except Exception as error:
        receipt['status']='PARTIAL';receipt['error_type']=type(error).__name__
    finally:
        for name in reversed(containers):
            try:cmd(['docker','rm','-f',name])
            except Exception:pass
        try:cmd(['docker','network','rm',network])
        except Exception:pass
        remaining=cmd(['docker','ps','-aq','--filter','label=nsai.owner='+tag]).decode().strip()
        nets=cmd(['docker','network','ls','-q','--filter','label=nsai.owner='+tag]).decode().strip()
        receipt['owned_resources_removed']=not remaining and not nets
        receipt['runner_source_unchanged']=receipt['source_sha256'][Path(__file__).relative_to(ROOT).as_posix()]==hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        write(dest,receipt);write(out/'current.json',{'receipt':dest.name,'status':receipt['status']})
        print(json.dumps({'run_id':tag,'status':receipt['status'],'owned_resources_removed':receipt['owned_resources_removed']}))
    return 0 if receipt['status']=='PASS_SCOPED' else 1

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--worker',type=int,choices=[4096,8192]);args=parser.parse_args()
    if args.worker:
        try:worker(args.worker)
        except Exception as error:
            # Request URLs are owned fixed literals; no paths, headers or secrets.
            print(json.dumps({'worker_error':dict(type=type(error).__name__,http_status=getattr(error,'code',None),message=str(error)[:180] if isinstance(error,(ValueError,KeyError)) else None)}),flush=True)
            sys.exit(1)
    else:sys.exit(main())
