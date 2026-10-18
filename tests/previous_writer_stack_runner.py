"""Owned previous-package write refusal after a private ledger event.

Not full old HTTP/UI compatibility or rollback approval. No live resources.
"""
import hashlib
import json
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import time
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import migrate
from check_release_readiness import source_snapshot
from qualify_local_stack import Stack

PREVIOUS='sha256:2ffe38c418aa16260baeaa9b6f0469ce9e58e84fdff792f7784746bef824113d'


def main():
    run=uuid4().hex;folder=ROOT/'evidence/previous-writer'/run
    stack=Stack(folder,'nsai-db-package-qualified:local','nsai-ocr-hardened-candidate:local')
    report=dict(status='FAIL',scope=__doc__,run_id=run,source_before=source_snapshot(ROOT),
        fixture_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        previous_image=PREVIOUS,current_image=stack.api_image,host_ports=False,live_services_accessed=False)
    def command(args,*,ok=True,timeout=60):
        result=subprocess.run(['docker',*args],capture_output=True,timeout=timeout)
        if ok and result.returncode:raise RuntimeError('Owned previous-writer command failed')
        return result
    try:
        command(['image','inspect',PREVIOUS])
        net=stack.network('data')
        with tempfile.TemporaryDirectory(prefix='nsai-previous-writer-') as temporary:
            password=secrets.token_hex(32);app_password=secrets.token_hex(32)
            token=Path(temporary)/'db';token.write_text(app_password,encoding='utf-8')
            db=stack.run('db',stack.db_image,['--tmpfs','/var/lib/postgresql/data:rw,nosuid,nodev,size=256m,mode=1777',
                '--tmpfs','/var/run/postgresql:rw,nosuid,nodev,size=8m,mode=1777','-e','POSTGRES_USER=nsai',
                '-e','POSTGRES_DB=nsai','-e','POSTGRES_PASSWORD='+password,'-e','PGDATA=/var/lib/postgresql/data/pgdata'],
                network=net,alias='db',user='70:70',memory='512m',pids='128')
            for _ in range(120):
                if command(['exec',db,'pg_isready','-h','127.0.0.1','-U','nsai'],ok=False).returncode==0:break
                time.sleep(.1)
            else:raise RuntimeError('Previous-writer database readiness deadline')
            stack.sql(db,migrate.migration_sql(ROOT)+migrate.role_sql(app_password))
            def worker(phase,image,program):
                name=stack.run(phase,image,['--mount','type=bind,source='+str(token)+',target=/run/token,readonly',
                    '-e','NSAI_DB_HOST=db','-e','NSAI_DB_NAME=nsai','-e','NSAI_DB_USER=nsai_app',
                    '-e','NSAI_DB_PASSWORD_FILE=/run/token','--entrypoint','python'],['-c',program],
                    network=net,memory='384m',pids='64')
                exit_code=command(['wait',name]).stdout.strip()
                logs=command(['logs',name],ok=False)
                (folder/(phase+'-output.json')).write_bytes(logs.stdout)
                (folder/(phase+'-errors.txt')).write_bytes(logs.stderr)
                assert exit_code==b'0','Previous-writer fixture failed; retained diagnostics'
                return json.loads(logs.stdout.strip().splitlines()[-1])
            report['initial']=worker('initial',PREVIOUS,"""import json
from nsai import store
result=store.store_document('Initial legacy source','Motor-A operating limit is 75 C.','old-writer-1')
assert result['created']
print(json.dumps(dict(created=True)))
""")
            previous=stack.sql(db,'SELECT nsai_audit_head();').strip().splitlines()[-1]
            body=dict(actor='local-user-alice',event_type='fixture.private',details={},previous_sha256=previous)
            digest=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(',',':')).encode()).hexdigest()
            stack.sql(db,"INSERT INTO audit_events(actor,event_type,details,previous_sha256,sha256,source_ids,provenance_complete) "
                f"VALUES('local-user-alice','fixture.private','{{}}','{previous}','{digest}',ARRAY[]::text[],true);")
            report['refusal']=worker('refusal',PREVIOUS,"""import json
from nsai import store
from psycopg.errors import SerializationFailure
try:store.store_document('Must roll back','Motor-B operating limit is 85 C.','old-writer-2')
except SerializationFailure:pass
else:raise AssertionError('Old package silently forked the ledger')
assert len(store.all_documents())==1
print(json.dumps(dict(stale_writer_refused=True,source_transaction_rolled_back=True)))
""")
            assert stack.sql(db,'SELECT count(*) FROM documents;').strip().splitlines()[-1]=='1'
            report['current']=worker('current',stack.api_image,"""import json
from nsai import store
result=store.store_document('Current writer','Motor-C operating limit is 95 C.','current-writer-1')
assert result['created']
print(json.dumps(dict(current_writer_succeeded=True)))
""")
            chain=stack.sql(db,"SELECT count(*) FILTER(WHERE previous_sha256 IS DISTINCT FROM expected),count(*) "
                "FROM (SELECT previous_sha256,lag(sha256,1,repeat('0',64)) OVER(ORDER BY id) expected FROM audit_events) ledger;").strip().splitlines()[-1]
            assert chain=='0|3'
            assert stack.sql(db,'SELECT count(*) FROM documents;').strip().splitlines()[-1]=='2'
            report['ledger_continuity_preserved']=True;report['status']='PASS_SCOPED'
    except Exception as error:
        report['failure_type']=type(error).__name__;report['failure']=str(error)[:500]
    finally:
        report['source_after']=source_snapshot(ROOT)
        if report['source_before']!=report['source_after']:report['status']='FAIL'
        stack.cleanup();report['cleanup_complete']=stack.receipt['cleanup_complete']
        if not report['cleanup_complete']:report['status']='FAIL'
        report['artifact_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.iterdir() if p.is_file() and p.name!='previous-writer-receipt.json'}
        (folder/'previous-writer-receipt.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=report['status'],run_id=run,cleanup=report['cleanup_complete'])))
    return 0 if report['status']=='PASS_SCOPED' else 1


if __name__=='__main__':raise SystemExit(main())
