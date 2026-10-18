"""Owned DB/encoder/application qualification with real checkpoint restart.

Uses packaged images, two internal networks, ephemeral credentials and no host
ports. The language model, private HTTP admission and release acceptance are not
qualified here. Existing live services and user volumes are never accessed.
"""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import secrets
import subprocess
import time
from uuid import uuid4
import migrate
from check_release_readiness import source_snapshot

ROOT=Path(__file__).resolve().parents[1]


def main():
    owner=uuid4().hex;run='nsai-semantic-'+owner[:12]
    folder=ROOT/'evidence/semantic-pipeline'/owner;folder.mkdir(parents=True)
    password=secrets.token_hex(32);app_password=secrets.token_hex(32)
    token=secrets.token_hex(32);api_token=secrets.token_hex(32)
    credentials=[password,app_password,token,api_token]
    networks=[run+'-data',run+'-encoder'];db=run+'-db';encoder=run+'-encoder-service'
    containers=[];created_networks=[]
    before=source_snapshot(ROOT)
    report=dict(status='FAIL',run_id=owner,recorded_at=datetime.now(timezone.utc).isoformat(),
        scope='Real PostgreSQL, HTTP encoder, route/storage functions and TestClient application lifecycle; not full UI, LLM or release acceptance',
        command=['python','scripts/qualify_semantic_pipeline.py'],source_before=before,
        host_ports=False,live_services_accessed=False,user_volumes_accessed=False,cleanup=[])
    def redact(text):
        for value in credentials:text=text.replace(value,'[owned credential]')
        return text
    def command(args,*,data=None,timeout=120,ok=True):
        result=subprocess.run(['docker',*args],input=data.encode('utf-8') if isinstance(data,str) else data,capture_output=True,timeout=timeout,cwd=ROOT)
        result.stdout=result.stdout.decode('utf-8');result.stderr=result.stderr.decode('utf-8',errors='replace')
        if ok and result.returncode:
            raise RuntimeError('Owned pipeline command failed: '+redact(result.stderr+result.stdout)[-2200:])
        return result
    def image(name):return command(['image','inspect',name,'--format','{{.Id}}']).stdout.strip()
    def sql(body):
        return command(['exec','-i',db,'psql','-X','-qAt','-v','ON_ERROR_STOP=1','-U','nsai','-d','nsai'],data=body).stdout.strip()
    def cleanup(kind,name):
        found=command(([kind,'inspect',name] if kind=='network' else ['inspect',name]),ok=False)
        if found.returncode:return True
        item=json.loads(found.stdout)[0]
        labels=item.get('Labels',{}) if kind=='network' else item['Config'].get('Labels',{})
        if labels.get('nsai.owner')!=owner:raise RuntimeError('Unowned pipeline cleanup refused')
        args=['network','rm',name] if kind=='network' else ['rm','--force',name]
        return command(args,ok=False).returncode==0
    def client(phase):
        name=run+'-client-'+phase;containers.append(name)
        command(['create','--name',name,'--label','nsai.owner='+owner,'--network',networks[0],
            '--read-only','--cap-drop','ALL','--security-opt','no-new-privileges:true','--user','10001:10001',
            '--pids-limit','96','--memory','768m','--cpus','1',
            '--tmpfs','/tmp:rw,nosuid,nodev,noexec,size=32m,mode=1777',
            '--mount','type=bind,source='+str(ROOT/'tests/semantic_pipeline_runtime_fixture.py')+',target=/qualification.py,readonly',
            '--mount','type=bind,source='+str(ROOT/'tests/semantic_fixture_helpers.py')+',target=/semantic_fixture_helpers.py,readonly',
            '-e','NSAI_DB_HOST='+db,'-e','NSAI_DB_NAME=nsai','-e','NSAI_DB_USER=nsai_app',
            '-e','NSAI_DB_PASSWORD_FILE=/tmp/db-password','-e','NSAI_API_TOKEN_FILE=/tmp/operator-token',
            '-e','NSAI_ENCODER_URL=http://encoder:8092','-e','NSAI_ENCODER_TOKEN_FILE=/tmp/encoder-token',
            '-e','NSAI_INDEX_WORKER_ENABLED=false','-i','--entrypoint','python',report['images']['api'],'-'])
        command(['network','connect',networks[1],name])
        prefix="from pathlib import Path\nimport sys\nsys.path.insert(0,'/')\n"
        for path,value in [('/tmp/db-password',app_password),('/tmp/operator-token',api_token),('/tmp/encoder-token',token)]:
            prefix+='Path('+repr(path)+').write_text('+repr(value)+')\n'
        prefix+='sys.argv=["/qualification.py",'+repr(phase)+']\n'
        prefix+='exec(compile(Path("/qualification.py").read_text(),"/qualification.py","exec"))\n'
        result=command(['start','--attach','--interactive',name],data=prefix,timeout=360)
        report.setdefault('phase_output_sha256',{})[phase]=hashlib.sha256(result.stdout.encode()).hexdigest()
        parsed=json.loads(result.stdout.strip().splitlines()[-1])
        if parsed['status']!='PASS_SCOPED':raise RuntimeError('Pipeline phase did not pass')
        return parsed
    try:
        report['images']=dict(api=image('nsai-implementation-candidate:local'),
                             encoder=image('nsai-cpu-encoder:qualification'),db=image('nsai-db-package-qualified:local'))
        report['fixture_sha256']={name:hashlib.sha256((ROOT/'tests'/name).read_bytes()).hexdigest()
            for name in ['semantic_pipeline_runtime_fixture.py','semantic_fixture_helpers.py']}
        report['model_manifest_sha256']=hashlib.sha256((ROOT/'state/models/all-MiniLM-L6-v2/manifest.json').read_bytes()).hexdigest()
        for network in networks:
            command(['network','create','--internal','--label','nsai.owner='+owner,network]);created_networks.append(network)
        containers.append(db)
        command(['run','-d','--name',db,'--label','nsai.owner='+owner,'--network',networks[0],
            '--memory','768m','--cpus','1','--pids-limit','128','--security-opt','no-new-privileges:true',
            '--tmpfs','/var/lib/postgresql/data:rw,nosuid,nodev,size=512m',
            '--tmpfs','/var/run/postgresql:rw,nosuid,nodev,size=8m',
            '-e','POSTGRES_USER=nsai','-e','POSTGRES_DB=nsai','-e','POSTGRES_PASSWORD='+password,report['images']['db']])
        for _ in range(60):
            if command(['exec',db,'pg_isready','-h','127.0.0.1','-U','nsai'],ok=False,timeout=10).returncode==0:break
            time.sleep(.25)
        else:raise RuntimeError('Owned pipeline database not ready')
        sql(migrate.migration_sql(ROOT)+migrate.role_sql(app_password))
        containers.append(encoder)
        wrapper="from pathlib import Path;Path('/tmp/encoder-token').write_text("+repr(token)+");import uvicorn;uvicorn.run('nsai.encoder_service:app',host='0.0.0.0',port=8092,access_log=False,log_level='warning')"
        command(['run','-d','--name',encoder,'--label','nsai.owner='+owner,'--network',networks[1],'--network-alias','encoder',
            '--read-only','--cap-drop','ALL','--security-opt','no-new-privileges:true','--user','10001:10001',
            '--pids-limit','64','--memory','768m','--cpus','2',
            '--tmpfs','/tmp:rw,nosuid,nodev,noexec,size=32m,mode=1777',
            '--mount','type=bind,source='+str(ROOT/'state/models/all-MiniLM-L6-v2')+',target=/models,readonly',
            '-e','NSAI_ENCODER_MODEL_DIR=/models','-e','NSAI_ENCODER_TOKEN_FILE=/tmp/encoder-token',
            '--entrypoint','python',report['images']['encoder'],'-c',wrapper])
        probe="import urllib.request;urllib.request.urlopen('http://127.0.0.1:8092/healthz',timeout=3)"
        for _ in range(60):
            if command(['exec',encoder,'python','-c',probe],ok=False,timeout=10).returncode==0:break
            time.sleep(.25)
        else:raise RuntimeError('Owned pipeline encoder not ready')
        report['checkpoint']=client('checkpoint')
        job_id=report['checkpoint']['job_id']
        if not isinstance(job_id,str) or len(job_id)!=64 or any(c not in '0123456789abcdef' for c in job_id):
            raise RuntimeError('Invalid owned job identity')
        # Owner-side fault injection models death/expiry without granting the
        # application maintenance privileges or waiting out a 300s lease.
        sql("UPDATE semantic_jobs SET lease_expires_at=clock_timestamp()-interval '1 second' WHERE id='"+job_id+"';")
        report['resume']=client('resume')
        report['database_final']=dict(
            jobs=sql('SELECT count(*) FROM semantic_jobs;'),
            succeeded=sql("SELECT count(*) FROM semantic_jobs WHERE state='succeeded';"),
            publications=sql('SELECT count(*) FROM semantic_publications;'),
            retained_checkpoints=sql('SELECT count(*) FROM semantic_job_vectors;'))
        assert report['database_final']==dict(jobs='5',succeeded='5',publications='5',retained_checkpoints='0')
        concurrent=report['resume']['concurrent_documents']
        if len(concurrent)!=2 or any(not isinstance(value,str) or len(value)!=32 or any(c not in '0123456789abcdef' for c in value) for value in concurrent):
            raise RuntimeError('Invalid owned concurrent document identities')
        literals=','.join("'"+value+"'" for value in concurrent)
        overlap=sql('SELECT EXISTS(SELECT 1 FROM semantic_jobs a JOIN semantic_publications pa ON pa.id=a.id '
            'JOIN semantic_jobs b ON b.id<>a.id JOIN semantic_publications pb ON pb.id=b.id '
            'WHERE a.document_id IN ('+literals+') AND b.document_id IN ('+literals+') '
            'AND a.last_claimed_at<pb.published_at AND b.last_claimed_at<pa.published_at);')
        report['two_worker_leases_overlap']=overlap=='t'
        if not report['two_worker_leases_overlap']:raise RuntimeError('Owned worker leases did not actually overlap')
        runtime=json.loads(command(['inspect',encoder]).stdout)[0]
        report['encoder_isolation']=dict(networks=sorted(runtime['NetworkSettings']['Networks']),
            mounts=[dict(target=m['Destination'],read_only=not m['RW']) for m in runtime['Mounts']],
            secret_environment_keys=[e.split('=',1)[0] for e in runtime['Config']['Env'] if e.startswith(('NSAI_DB_','NSAI_API_'))])
        assert report['encoder_isolation']['networks']==[networks[1]]
        assert report['encoder_isolation']['secret_environment_keys']==[]
        report['source_after']=source_snapshot(ROOT)
        if report['source_after']!=before:raise RuntimeError('Source changed during pipeline qualification')
        report['fixture_after_sha256']={name:hashlib.sha256((ROOT/'tests'/name).read_bytes()).hexdigest()
            for name in report['fixture_sha256']}
        if report['fixture_after_sha256']!=report['fixture_sha256']:
            raise RuntimeError('Fixture changed during pipeline qualification')
        report['status']='PASS_SCOPED'
    except Exception as error:
        report['failure']=dict(type=type(error).__name__,message=redact(str(error))[:2400])
    finally:
        for name in reversed(containers):
            report['cleanup'].append(dict(kind='container',name=name,removed=cleanup('container',name)))
        for name in reversed(created_networks):
            report['cleanup'].append(dict(kind='network',name=name,removed=cleanup('network',name)))
        if not all(item['removed'] for item in report['cleanup']):report['status']='FAIL'
        (folder/'receipt.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=report['status'],run_id=owner,
        checks=sum(len(report.get(phase,{}).get('checks',[])) for phase in ['checkpoint','resume']),
        cleanup=all(item['removed'] for item in report['cleanup']))))
    return 0 if report['status']=='PASS_SCOPED' else 1


if __name__=='__main__':raise SystemExit(main())
