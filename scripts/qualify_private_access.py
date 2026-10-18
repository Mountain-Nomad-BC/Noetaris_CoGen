"""Record reproducible, narrowly scoped private-policy persistence evidence.

Creates only isolated ephemeral test containers and local evidence. This does
not migrate the live database or certify the unfinished content adapter.
"""
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4
import xml.etree.ElementTree as ET
from check_release_readiness import source_snapshot

ROOT = Path(__file__).resolve().parents[1]


def package_hashes(image,owner):
    program="""import hashlib,json
from pathlib import Path
root=Path('/app');paths=[]
for area in ('src','assets','database','LICENSES'):
 paths.extend(p for p in (root/area).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc')
paths.extend(root/p for p in ('deploy/init.sql','LICENSE','NOTICE'))
print(json.dumps({p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}))
"""
    name='nsai-private-package-check-'+owner[:12]
    try:
        result=subprocess.run(['docker','run','--rm','--name',name,'--label','nsai.owner='+owner,
            '--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges:true',
            '--user','10001:10001','--cpus','1','--memory','256m','--pids-limit','32',
            '--entrypoint','python',image,'-c',program],capture_output=True,timeout=90)
        if result.returncode:raise RuntimeError('Packaged source inspector failed')
        return json.loads(result.stdout)
    finally:
        inspected=subprocess.run(['docker','inspect',name],capture_output=True,timeout=30)
        if inspected.returncode==0:
            value=json.loads(inspected.stdout)[0]
            if value['Config'].get('Labels',{}).get('nsai.owner')!=owner:
                raise RuntimeError('Source inspector ownership changed')
            subprocess.run(['docker','rm','--force',name],capture_output=True,check=True,timeout=30)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-only',action='store_true')
    parser.add_argument('--workers',type=int,choices=[1,2],default=1)
    parser.add_argument('--timings',type=Path)
    args=parser.parse_args()
    if args.timings is not None:
        if args.workers!=2 or not args.timings.resolve().is_relative_to(ROOT/'evidence') or args.timings.stat().st_size>8*1024*1024:
            parser.error('Historical timing hints require the explicit two-worker profile and bounded local evidence')
    image = subprocess.run(['docker', 'image', 'inspect', 'postgres:16-alpine',
                            '--format', '{{.Id}}'], capture_output=True, text=True, timeout=30)
    if image.returncode:
        raise SystemExit('Local PostgreSQL qualification image unavailable')
    image_id = image.stdout.strip()
    if not image_id.startswith('sha256:') or len(image_id) != 71:
        raise SystemExit('Invalid qualification image identity')
    application = subprocess.run(['docker','image','inspect','nsai-implementation-candidate:local',
                                 '--format','{{.Id}}'],capture_output=True,text=True,timeout=30)
    application_id=application.stdout.strip()
    if application.returncode or not application_id.startswith('sha256:') or len(application_id)!=71:
        raise SystemExit('Local application qualification image unavailable')
    run_id = uuid4().hex
    folder = ROOT/'evidence/private-access'/run_id
    folder.mkdir(parents=True)
    def hashes():
        values=source_snapshot(ROOT)
        for path in (ROOT/'tests').rglob('*.py'):
            if path.is_symlink():raise RuntimeError('Test source link is not admitted')
            values[path.relative_to(ROOT).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
        return values
    before = hashes()
    expected={path:value for path,value in before.items() if
        path.startswith(('src/','assets/','database/migrations/','LICENSES/')) or
        path in {'database/access-contract.json','deploy/init.sql','LICENSE','NOTICE'}}
    verified=False;failure=None
    try:
        actual=package_hashes(application_id,run_id)
        (folder/'packaged-source.json').write_text(json.dumps(actual,indent=2)+'\n',encoding='utf-8')
        verified=actual==expected
        if not verified:failure='Packaged source differs from current source; rebuild before qualification'
    except (RuntimeError,OSError,ValueError,subprocess.SubprocessError) as error:
        failure=type(error).__name__
    environment = dict(os.environ, NSAI_TEST_PRIVATE_DATABASE='1',
                       NSAI_TEST_PRIVATE_DATABASE_IMAGE=image_id,
                       NSAI_TEST_PRIVATE_APPLICATION_IMAGE=application_id,
                       NSAI_TEST_PRIVATE_OWNER=run_id,NSAI_TEST_PRIVATE_PACKAGED_SOURCE='1',PYTHONUNBUFFERED='1',
                       PYTHONUTF8='1',PYTHONIOENCODING='utf-8')
    environment.pop('PYTEST_ADDOPTS',None)
    command = [sys.executable, '-m', 'pytest', '-q', '--maxfail=1', '--junitxml='+str(folder/'tests.xml')]
    timed_out=False
    worker_result=None;cleanup=None;cleanup_failure=None
    pytest_executed=verified and not args.verify_only
    with (folder/'pytest.txt').open('x',encoding='utf-8') as output:
        try:
            if pytest_executed and args.workers==2:
                from qualification_shards import execute
                worker_result=execute(ROOT,folder,environment,workers=2,timings=args.timings)
                timed_out=worker_result['timed_out']
                result=subprocess.CompletedProcess(command,worker_result['exit_code'])
                output.write(json.dumps(worker_result,indent=2)+'\n')
            else:
                result = subprocess.run(command,cwd=ROOT,env=environment,text=True,
                                        stdout=output,stderr=subprocess.STDOUT,timeout=1800) if pytest_executed else subprocess.CompletedProcess(command,0 if verified else 2)
        except subprocess.TimeoutExpired:
            timed_out=True
            result=subprocess.CompletedProcess(command,124)
        except (RuntimeError,OSError,ValueError,ET.ParseError) as error:
            failure=type(error).__name__;result=subprocess.CompletedProcess(command,1)
        finally:
            from qualification_shards import cleanup_owned
            try:cleanup=cleanup_owned(run_id)
            except (RuntimeError,OSError,ValueError,subprocess.SubprocessError) as error:cleanup_failure=type(error).__name__
    after = hashes()
    suites = ET.parse(folder/'tests.xml').getroot().findall('testsuite') if (folder/'tests.xml').exists() else []
    counts = {key: sum(int(s.get(key, '0')) for s in suites)
              for key in ['tests','failures','errors','skipped']}
    completed=(args.verify_only or pytest_executed and counts['tests']>0
               and not any(counts[key] for key in ('failures','errors','skipped')))
    display_command=command
    if args.verify_only or args.workers==2:
        display_command=[sys.executable,'scripts/qualify_private_access.py',*sys.argv[1:]]
    report = dict(schema_version='nsai.private-policy-qualification/1', run_id=run_id,
                  recorded_at=datetime.now(timezone.utc).isoformat(),
                  status=('PASS_IMAGE_SOURCE_BYTES_ONLY' if args.verify_only else 'PASS') if result.returncode == 0 and before == after and cleanup_failure is None and completed else 'FAIL',
                  scope='Policy persistence and regression suite; not full private access or release acceptance',
                  postgres_image_id=image_id,application_image_id=application_id,
                  application_source_mode='Host Python unit tests; DB application fixtures use byte-verified packaged source and mounted owned test helpers',
                  host_python_version=sys.version,packaged_source_verified=verified,pytest_executed=pytest_executed,failure=failure,
                  command=display_command,
                  execution_profile=dict(workers=args.workers,overall_test_budget_seconds=1800,whole_file_groups=True),
                  worker_result=worker_result,cleanup=cleanup,cleanup_failure=cleanup_failure,
                  exit_code=result.returncode, counts=counts, source_sha256=before,
                  timed_out=timed_out,cleanup_requires_inspection=cleanup_failure is not None,
                  sources_unchanged=before == after,
                  artifacts={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                             for p in folder.iterdir() if p.is_file() and p.name!='receipt.json'},
                  unqualified=['private HTTP admission and full UI-to-backend journeys',
                               'held-out retrieval and grounded-answer quality',
                               'full derived-surface adversarial acceptance',
                               'PDF highlighting, capacity, independent security and release acceptance'])
    (folder/'receipt.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['status','run_id','exit_code','counts']}))
    return 0 if report['status'] in {'PASS','PASS_IMAGE_SOURCE_BYTES_ONLY'} else 1


if __name__ == '__main__':
    raise SystemExit(main())
