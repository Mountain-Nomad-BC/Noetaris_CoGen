"""Restore an owned integration backup in a disposable, network-isolated DB.

Checks quiescent table content, schema access definitions and the audit chain.
Never selects the original application database, publishes ports or deletes data.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import secrets
import subprocess
import sys
import time
from uuid import uuid4

import start_integration as integration

ROOT=integration.ROOT
STATE=integration.STATE


def main():
    owner=uuid4().hex;name='noetaris-recovery-'+owner
    folder=STATE/'recovery'/owner;folder.mkdir(parents=True)
    report=dict(run_id=owner,status='FAIL',scope=__doc__,host_ports=False,original_stack_accessed=False,
                producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    created=False
    compose=['docker','compose','-p',integration.PROJECT,'-f',str(STATE/'compose.json')]
    def sql(container,body):
        return integration.run(['docker','exec','-i',container,'psql','-X','-qAt','-v','ON_ERROR_STOP=1','-U','nsai','-d','nsai'],body=body)
    try:
        source=integration.run(compose+['ps','-q','db'])
        info=json.loads(integration.run(['docker','inspect',source]))[0]
        if (info['Config'].get('Labels',{}).get('com.docker.compose.project')!=integration.PROJECT or
            not any(m.get('Name')==integration.PROJECT+'_integration_data' for m in info['Mounts'])):
            raise RuntimeError('Refusing unowned source database')
        image=info['Image'];report['database_image']=image
        tables=sql(source,"SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename").splitlines()
        if not tables or any(re.fullmatch('[a-z_][a-z0-9_]*',t) is None for t in tables):
            raise RuntimeError('Invalid owned table inventory')
        # Aggregate digests only; never retain private table rows in the receipt.
        query='SET statement_timeout=20000;\n'+'\n'.join(
            f"SELECT '{table}',count(*),md5(coalesce(string_agg(to_jsonb(t)::text,E'\\n' ORDER BY to_jsonb(t)::text),'')) FROM public.\"{table}\" t;"
            for table in tables)
        before=sql(source,query)
        spec=importlib.util.spec_from_file_location('owned_recovery_migrate',ROOT/'scripts/migrate.py')
        migrate=importlib.util.module_from_spec(spec);spec.loader.exec_module(migrate)
        backup=folder/'database.sql'
        migrate.stream_backup(['docker','exec',source,'pg_dump','-U','nsai','-d','nsai'],backup)
        after=sql(source,query)
        if before!=after:raise RuntimeError('Integration writes occurred during quiescent recovery qualification')
        manifest=json.loads(backup.with_suffix('.sql.manifest.json').read_text())
        report['backup_sha256']=hashlib.sha256(backup.read_bytes()).hexdigest()
        report['backup_bytes']=backup.stat().st_size
        if (manifest.get('sha256')!=report['backup_sha256'] or
            type(manifest.get('size_bytes')) is not int or manifest['size_bytes']!=report['backup_bytes']):
            raise RuntimeError('Backup manifest does not match exact dump bytes')
        integration.run(['docker','run','-d','--name',name,'--label','nsai.owner='+owner,'--network','none',
            '--read-only','--cap-drop','ALL','--security-opt','no-new-privileges:true','--pids-limit','128',
            '--cpus','1','--memory','768m','--user','70:70',
            '--tmpfs','/tmp:rw,nosuid,noexec,size=32m,mode=1777',
            '--tmpfs','/var/run/postgresql:rw,nosuid,size=8m,mode=1777',
            '--tmpfs','/var/lib/postgresql/data:rw,nosuid,noexec,size=512m,mode=1777',
            '-e','POSTGRES_HOST_AUTH_METHOD=trust','-e','POSTGRES_USER=nsai','-e','POSTGRES_DB=nsai',
            '-e','PGDATA=/var/lib/postgresql/data/pgdata',image])
        created=True
        for _ in range(100):
            ready=subprocess.run(['docker','exec',name,'pg_isready','-h','127.0.0.1','-U','nsai'],capture_output=True,timeout=10)
            if ready.returncode==0:break
            time.sleep(.2)
        else:raise RuntimeError('Owned restore database readiness deadline')
        password=secrets.token_hex(32)
        password_file=folder/'app_db.txt';password_file.write_text(password,encoding='ascii')
        sql(name,"CREATE ROLE nsai_app LOGIN PASSWORD '"+password+"';")
        with backup.open('rb') as stream:
            result=subprocess.run(['docker','exec','-i',name,'psql','-X','-q','-v','ON_ERROR_STOP=1','-U','nsai','-d','nsai'],
                                  stdin=stream,capture_output=True,timeout=120)
        if result.returncode:raise RuntimeError('Owned restore failed; credential-bearing diagnostics withheld')
        # pg_dump without --create does not recreate database-level grants.
        # Reapply the same least-privilege role contract before startup checks.
        sql(name,'BEGIN;'+migrate.role_sql(password))
        restored=sql(name,query)
        if restored!=before:raise RuntimeError('Restored table contents do not match quiescent source')
        sys.path.insert(0,str(ROOT/'src'))
        from nsai.schema_contract import ACCESS_DEFINITIONS_SQL,definitions_hash
        definitions=json.loads(sql(name,'SET ROLE nsai_app;'+ACCESS_DEFINITIONS_SQL))
        expected=json.loads((ROOT/'database/access-contract.json').read_text())
        if definitions_hash(definitions)!=expected['definitions_sha256']:
            raise RuntimeError('Restored access contract differs')
        application=json.loads((STATE/'identity.json').read_text())['images']['api']
        report['application_image']=application
        code="""import json
from nsai import store,workflow_store
with store.identity_context(dict(actor='local-reviewer',role='reviewer',permissions=['read','review'])):
    report=workflow_store.audit_report()
    assert report['valid'] is True
    print(json.dumps({'audit_chain_valid':True}))
"""
        audit=json.loads(integration.run(['docker','run','--rm','--network','container:'+name,
            '--read-only','--cap-drop','ALL','--security-opt','no-new-privileges:true',
            '--pids-limit','64','--memory','256m','--cpus','1',
            '--tmpfs','/tmp:rw,nosuid,noexec,size=16m,mode=1777',
            '--mount','type=bind,source='+password_file.resolve().as_posix()+',target=/run/restore_password,readonly',
            '-e','NSAI_DB_HOST=127.0.0.1','-e','NSAI_DB_NAME=nsai','-e','NSAI_DB_USER=nsai_app',
            '-e','NSAI_DB_PASSWORD_FILE=/run/restore_password','--entrypoint','python',application,'-c',code]))
        report.update(status='PASS',table_count=len(tables),table_digest_sha256=hashlib.sha256(before.encode()).hexdigest(),
                      exact_table_contents=True,access_contract_verified=True,audit_chain_valid=audit['audit_chain_valid'],quiescent_only=True,
                      roles_converged_after_restore=True,concurrent_write_or_pitr_proof=False)
    except Exception as error:
        report.update(failure_type=type(error).__name__,failure=str(error))
    finally:
        report['cleanup_complete']=not created
        if created:
            try:
                labels=json.loads(integration.run(['docker','inspect',name]))[0]['Config'].get('Labels',{})
                if labels.get('nsai.owner')!=owner:raise RuntimeError('Owned cleanup identity mismatch')
                integration.run(['docker','rm','-f',name]);report['cleanup_complete']=True
            except Exception:
                report['cleanup_complete']=False;report['status']='FAIL'
        (folder/'receipt.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        password_file=folder/'app_db.txt'
        if password_file.exists():password_file.unlink()
    print(json.dumps(report,indent=2))
    return 0 if report['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
