"""Owned bounded PostgreSQL lexical omission qualification without model/API access."""
import importlib.util,json,secrets,subprocess,tempfile,shutil,hashlib
from pathlib import Path
from qualify_local_stack import Stack,ROOT,command

def main():
    stack=Stack(ROOT/'evidence/implementation/retrieval-coverage','nsai-db-package-qualified:local','nsai-ocr-hardened-candidate:local')
    spec=importlib.util.spec_from_file_location('coverage_migrate',ROOT/'scripts/migrate.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    try:
        with tempfile.TemporaryDirectory(prefix=stack.prefix) as folder:
            folder=Path(folder);key=secrets.token_hex(32);secret=folder/'db.txt';secret.write_text(key)
            network=stack.network('db');db=stack.db('db',network,secrets.token_hex(32));command(['docker','update','--cpus','.25','--memory','384m',db])
            stack.sql(db,m.migration_sql(ROOT)+'COMMIT;');stack.sql(db,'BEGIN;'+m.role_sql(key,include_commit=False)+'COMMIT;')
            snapshot=folder/'src';shutil.copytree(ROOT/'src',snapshot,ignore=shutil.ignore_patterns('__pycache__'))
            stack.receipt['snapshot_source_sha256']={p.relative_to(snapshot).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in snapshot.rglob('*') if p.is_file()}
            options=['--cpus','.75','--mount',f'type=bind,source={snapshot},target=/qualified/src,readonly','--mount',f'type=bind,source={ROOT / "tests/retrieval_coverage_pg_fixture.py"},target=/qualified/fixture.py,readonly','--mount',f'type=bind,source={secret},target=/run/secrets/db,readonly','--env','PYTHONPATH=/qualified/src','--env','NSAI_DB_HOST=db','--env','NSAI_DB_USER=nsai_app','--env','NSAI_DB_NAME=nsai','--env','NSAI_DB_PASSWORD_FILE=/run/secrets/db']
            options+=['--mount',f'type=bind,source={ROOT / "assets"},target=/qualified/assets,readonly']
            worker=stack.run('retrieval',stack.api_image,options,['python','/qualified/fixture.py'],network=network,memory='384m')
            waited=subprocess.run(['docker','wait',worker],capture_output=True,timeout=60,check=True);logs=subprocess.run(['docker','logs',worker],capture_output=True,check=True)
            (stack.output/'stdout.json').write_bytes(logs.stdout);(stack.output/'stderr.txt').write_bytes(logs.stderr)
            result=json.loads(logs.stdout);stack.receipt.update(status='PASS' if result['all_pass'] else 'FAIL',result=result,fixture_exit_code=int(waited.stdout),no_models=True,no_production_resources=True,aggregate_cpu_cap=1,aggregate_memory_mib=768)
            policy=json.loads(command(['docker','inspect',db,worker]));stack.receipt['resource_policies']=[dict(nano_cpus=p['HostConfig']['NanoCpus'],memory=p['HostConfig']['Memory'],readonly=p['HostConfig']['ReadonlyRootfs'],no_ports=not p['HostConfig']['PortBindings']) for p in policy]
            assert sum(p['nano_cpus'] for p in stack.receipt['resource_policies'])==1000000000 and sum(p['memory'] for p in stack.receipt['resource_policies'])==768*1024*1024
    except Exception as error:stack.receipt.update(status='FAIL',failure_type=type(error).__name__);raise
    finally:stack.cleanup()
    print(json.dumps({'status':stack.receipt['status'],'cleanup':stack.receipt['cleanup_complete']}));return 0 if stack.receipt['status']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
