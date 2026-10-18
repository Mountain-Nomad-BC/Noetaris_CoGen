"""Private command receipts; public summaries require separately reviewed projection."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib
import json
import subprocess
import sys
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]

def main():
    raw=ROOT/'evidence/raw';raw.mkdir(parents=True,exist_ok=True)
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid4().hex[:12]
    run_root=raw/run_id; run_root.mkdir()
    commands=[('unit-tests',[sys.executable,'-m','pytest','-q','--tb=short']),
        ('compose-static',[sys.executable,'scripts/validate_compose_security.py']),
        ('compose-effective',['docker','compose','-f','compose.yaml','-f','deploy/local/compose.cpu.yaml','config','--quiet']),
        ('compose-ollama-candidate',['docker','compose','-f','compose.yaml','-f','deploy/local/compose.ollama.yaml','--profile','local-ai','config','--quiet']),
        ('fixture-baseline',[sys.executable,'evaluations/run_fixture_baseline.py']),
        ('javascript-syntax',['node','--check','assets/app.js'])]
    receipts=[]
    for name,command in commands:
        started=datetime.now(timezone.utc)
        try:
            result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=300)
            output=result.stdout+result.stderr
        except (OSError,subprocess.TimeoutExpired) as error:
            result=subprocess.CompletedProcess(command,124 if isinstance(error,subprocess.TimeoutExpired) else 127)
            output=type(error).__name__+': command did not finish successfully; raw exception text withheld'
        (run_root/(name+'.txt')).write_text(output,encoding='utf-8')
        receipts.append(dict(name=name,command=command,exit_code=result.returncode,status='PASS' if result.returncode==0 else 'FAIL',
            captured_at=started.isoformat(),output_file='evidence/raw/'+run_id+'/'+name+'.txt',output_sha256=hashlib.sha256(output.encode()).hexdigest()))
        print(name,receipts[-1]['status'])
    inventory={}
    for directory in ('src','assets','database','deploy','scripts','tests'):
        for path in (ROOT/directory).rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts and path.name!='verification.json':
                inventory[path.relative_to(ROOT).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
    for name in ('Dockerfile','compose.yaml','pyproject.toml','requirements.lock'):
        path=ROOT/name
        if path.exists(): inventory[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    (raw/'source-inventory.json').write_text(json.dumps(inventory,indent=2))
    extras={}
    evidence_errors=[]
    now=datetime.now(timezone.utc)
    source_hash=hashlib.sha256((raw/'source-inventory.json').read_bytes()).hexdigest()
    for filename in ('live-system-current.json','persistence.json','browser.json','session-isolation.json','recovery.json','runtime-controls.json','parser-runtime-controls.json','model-auth-controls.json','image-scan-summary.json','cpu-model-provenance.json','runtime-dependency-audit.json','secret-hygiene.json'):
        path=raw/filename
        if path.exists():
            try:extras[filename]=json.loads(path.read_text(encoding='utf-8-sig'))
            except (ValueError,UnicodeError):extras[filename]={'status':'UNVERIFIED','reason':'Evidence could not be decoded'}
        else:extras[filename]={'status':'MISSING','reason':'No recorded evidence available'}
    for filename,item in extras.items():
        if not isinstance(item,dict):
            evidence_errors.append(filename+': invalid evidence envelope'); extras[filename]={'status':'UNVERIFIED'}; continue
        stamp=item.get('captured_at')
        try:
            age=(now-datetime.fromisoformat(stamp.replace('Z','+00:00'))).total_seconds()
            if age<0 or age>86400: evidence_errors.append(filename+': stale or future evidence')
        except (ValueError,TypeError,AttributeError):
            evidence_errors.append(filename+': missing timestamp')
        if item.get('source_inventory_sha256')!=source_hash:
            evidence_errors.append(filename+': evidence does not bind current source')
        if item.get('status')!='PASS' and item.get('passed') is not True:
            evidence_errors.append(filename+': missing successful verdict')
    model_result=next((r.get('details',{}) for r in extras.get('live-system-current.json',{}).get('results',[]) if r['name']=='real CPU model inference and resolving citations'),{})
    summary=dict(run_id=run_id,overall_status='FAIL' if evidence_errors or any(r['exit_code'] for r in receipts) else 'PASS', evidence_errors=evidence_errors,captured_at=datetime.now(timezone.utc).isoformat(),receipts=receipts,
        source_inventory_sha256=hashlib.sha256((raw/'source-inventory.json').read_bytes()).hexdigest(),
        local_security='active',central_security='disabled',amd_gpu_validation='PENDING',
        evidence_files=list(extras),
        live_acceptance={'passed':extras.get('live-system-current.json',{}).get('passed',False),'checks':len(extras.get('live-system-current.json',{}).get('results',[])),'real_model_tested':extras.get('live-system-current.json',{}).get('model_required',False)},
        persistence=extras.get('persistence.json',{}).get('status','PENDING'),
        browser=extras.get('browser.json',{}).get('status','PENDING'),
        session_isolation=extras['session-isolation.json'].get('status','UNVERIFIED'),
        backup_restore=extras['recovery.json'].get('status','UNVERIFIED'),
        runtime_controls=extras.get('runtime-controls.json',{}),
        parser_controls=extras.get('parser-runtime-controls.json',{}),
        model_authentication=extras.get('model-auth-controls.json',{}),
        real_model_sample={key:model_result.get(key) for key in ('mode','provider','model','latency_ms','citation_validation')},
        image_scans=extras.get('image-scan-summary.json',{}),
        model_artifact=extras.get('cpu-model-provenance.json',{}),
        runtime_dependency_vulnerabilities=sum(len(d.get('vulns',[])) for d in extras['runtime-dependency-audit.json']['dependencies']) if 'dependencies' in extras['runtime-dependency-audit.json'] else None,
        limitations=['AMD GPU execution pending','Central adapter staged, inactive','No arbitrary generated-code execution','Lexical retrieval, no embeddings','No OCR','Local audit chain not externally anchored','Private source publication blocked','Container CVE scan status separately documented'])
    # Raw legacy metadata includes local paths and diagnostics. Never publish it
    # through the static asset tree or overwrite the reviewed summary projection.
    summary['certification']=False
    summary['publication_reviewed']=False
    (run_root/'verification-receipts.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    (raw/'verification-receipts.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    return 1 if evidence_errors or any(r['exit_code'] for r in receipts) else 0

if __name__ == "__main__":
    raise SystemExit(main())
