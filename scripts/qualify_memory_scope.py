"""Owned real PostgreSQL memory-scope regression; no live API/model access."""
import argparse,importlib.util,json,secrets,subprocess,tempfile,shutil
from pathlib import Path
from uuid import uuid4
from qualify_local_stack import Stack,ROOT

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=['before','after'],required=True);args=parser.parse_args()
    output=ROOT/'evidence/implementation/memory-scope'/(args.phase+'-'+uuid4().hex)
    stack=Stack(output,'nsai-db-package-qualified:local','nsai-ocr-hardened-candidate:local')
    spec=importlib.util.spec_from_file_location('memory_migrate',ROOT/'scripts/migrate.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    try:
        with tempfile.TemporaryDirectory(prefix=stack.prefix) as folder:
            key=secrets.token_hex(32);secret=Path(folder)/'db.txt';secret.write_text(key)
            network=stack.network('db');db=stack.db('db',network,secrets.token_hex(32))
            stack.sql(db,m.migration_sql(ROOT)+'COMMIT;');stack.sql(db,'BEGIN;'+m.role_sql(key,include_commit=False)+'COMMIT;')
            import sys
            sys.path.insert(0,str(ROOT/'src'))
            from nsai.schema_contract import ACCESS_DEFINITIONS_SQL,expected_access_contract
            actual=json.loads(stack.sql(db,'SET ROLE nsai_app; '+ACCESS_DEFINITIONS_SQL).strip().splitlines()[-1])
            expected=expected_access_contract()['definitions']
            differences={name:dict(expected=expected[name],actual=actual[name]) for name in expected if expected[name]!=actual[name]}
            (output/'definition-differences.json').write_text(json.dumps(differences,indent=2))
            if differences:raise RuntimeError('Owned database definition mismatch; inspect retained differences')
            snapshot=Path(folder)/'src';shutil.copytree(ROOT/'src',snapshot,ignore=shutil.ignore_patterns('__pycache__'))
            if args.phase=='before':
                source=snapshot/'nsai/workflow_store.py';text=source.read_text();start=text.index('def memory_context(');end=text.index('\ndef propose_learning',start)
                original=(ROOT/'evidence/implementation/memory-scope/original-memory-context.txt').read_text();source.write_text(text[:start]+original+text[end:])
            # Keep package-relative schema admission bound to the same candidate
            # migration/definition manifest while testing a copied source tree.
            options=['--mount',f'type=bind,source={snapshot},target=/app/src,readonly','--mount',f'type=bind,source={ROOT / "tests/memory_scope_pg_fixture.py"},target=/qualification.py,readonly','--mount',f'type=bind,source={ROOT / "tests/semantic_fixture_helpers.py"},target=/semantic_fixture_helpers.py,readonly','--mount',f'type=bind,source={secret},target=/run/secrets/db,readonly','--env','PYTHONPATH=/app/src:/','--env','NSAI_DB_HOST=db','--env','NSAI_DB_USER=nsai_app','--env','NSAI_DB_NAME=nsai','--env','NSAI_DB_PASSWORD_FILE=/run/secrets/db']
            worker=stack.run('memory',stack.api_image,options,['python','/qualification.py'],network=network,memory='384m')
            waited=subprocess.run(['docker','wait',worker],capture_output=True,timeout=60,check=True)
            logs=subprocess.run(['docker','logs',worker],capture_output=True,check=True)
            (output/'stdout.json').write_bytes(logs.stdout);(output/'stderr.txt').write_bytes(logs.stderr)
            result=json.loads(logs.stdout);stack.receipt.update(status='PASS' if result['all_pass'] and int(waited.stdout)==0 else 'FAIL',result=result,fixture_exit_code=int(waited.stdout),no_real_model_calls=True,synthetic_encoder=True,no_production_resources=True)
    except Exception as error:stack.receipt.update(status='FAIL',failure_type=type(error).__name__);raise
    finally:stack.cleanup()
    print(json.dumps({'phase':args.phase,'status':stack.receipt['status'],'cleanup':stack.receipt['cleanup_complete']}))
    return 0 if stack.receipt['status']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
