"""Build/check the packaged access definition baseline in an owned empty DB."""
import argparse
import hashlib
import json
from pathlib import Path
import secrets
import subprocess
import time
from uuid import uuid4
import sys
import migrate

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from nsai.schema_contract import ACCESS_DEFINITIONS_SQL,expected_migrations,definitions_hash


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true')
    args=parser.parse_args()
    run=uuid4().hex;name='nsai-access-contract-'+run[:12]
    folder=ROOT/'evidence/access-contract-builds'/run;folder.mkdir(parents=True)
    password=secrets.token_hex(32)
    before=expected_migrations()
    helper_before=hashlib.sha256((ROOT/'src/nsai/schema_contract.py').read_bytes()).hexdigest()
    report=dict(status='FAIL',run_id=run,scope='Owned clean database access definition baseline; not independent acceptance',
                live_resources_accessed=False,host_ports=False,write_requested=args.write)
    created=False
    def command(arguments,*,data=None,ok=True):
        result=subprocess.run(['docker',*arguments],input=data.encode('utf-8') if isinstance(data,str) else data,capture_output=True,timeout=90)
        result.stdout=result.stdout.decode('utf-8');result.stderr=result.stderr.decode('utf-8',errors='replace')
        if ok and result.returncode:
            (folder/'command-failure-stderr.txt').write_text(result.stderr,encoding='utf-8')
            raise RuntimeError('Owned access contract command failed')
        return result
    def sql(body):
        return command(['exec','-i',name,'psql','-X','-qAt','-v','ON_ERROR_STOP=1','-U','postgres','-d','nsai'],data=body).stdout.strip()
    try:
        image=command(['image','inspect','postgres:16-alpine','--format','{{.Id}}']).stdout.strip()
        if len(image)!=71 or not image.startswith('sha256:'):raise RuntimeError('Invalid database image identity')
        report['database_image']=image
        command(['run','-d','--name',name,'--label','nsai.owner='+run,'--network','none',
            '--memory','256m','--cpus','1','--tmpfs','/var/lib/postgresql/data:rw,noexec,nosuid,size=192m',
            '-e','POSTGRES_HOST_AUTH_METHOD=trust','-e','POSTGRES_DB=nsai',image]);created=True
        for _ in range(120):
            if command(['exec',name,'pg_isready','-h','127.0.0.1','-U','postgres'],ok=False).returncode==0:break
            time.sleep(.1)
        else:raise RuntimeError('Owned database did not become ready')
        if sql("SELECT current_setting('server_version_num')::integer/10000;")!='16':
            raise RuntimeError('Database major version is not admitted')
        sql(migrate.migration_sql(ROOT)+migrate.role_sql(password))
        definitions=json.loads(sql('SET ROLE nsai_app; '+ACCESS_DEFINITIONS_SQL))
        expected_migrations.cache_clear()
        if expected_migrations()!=before or hashlib.sha256((ROOT/'src/nsai/schema_contract.py').read_bytes()).hexdigest()!=helper_before:
            raise RuntimeError('Access contract source changed during generation')
        contract=dict(schema_version='nsai.database-access-contract/1',postgres_major=16,
            migration_sha256=before,query_sha256=hashlib.sha256(ACCESS_DEFINITIONS_SQL.encode()).hexdigest(),
            definitions_sha256=definitions_hash(definitions),definitions=definitions,
            producer=dict(database_image=image,run_id=run,scope=report['scope'],schema_contract_sha256=helper_before,
                          script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
        path=ROOT/'database/access-contract.json'
        current=json.loads(path.read_bytes()) if path.exists() else {}
        keys=['schema_version','postgres_major','migration_sha256','query_sha256','definitions_sha256','definitions']
        matches=all(current.get(key)==contract[key] for key in keys)
        if not matches and args.write:
            if path.is_symlink():raise RuntimeError('Access contract link is not admitted')
            path.write_text(json.dumps(contract,indent=2)+'\n',encoding='utf-8')
            report['changed']=True
        elif not matches:raise RuntimeError('Packaged access contract differs from clean migrations')
        report.update(status='PASS',definitions_sha256=contract['definitions_sha256'],
                      contract_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    except (RuntimeError,OSError,ValueError,subprocess.SubprocessError) as error:
        report['failure_type']=type(error).__name__
    finally:
        report['cleanup']=not created
        if created:
            inspected=command(['inspect',name],ok=False)
            if inspected.returncode==0 and json.loads(inspected.stdout)[0]['Config'].get('Labels',{}).get('nsai.owner')==run:
                report['cleanup']=command(['rm','--force',name],ok=False).returncode==0
            if not report['cleanup']:report['status']='FAIL'
        (folder/'receipt.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report))
    return 0 if report['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
