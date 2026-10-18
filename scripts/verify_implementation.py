"""Qualify candidate changes using owned resources only, never live user volumes."""
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
import importlib.util,json,subprocess,time,hashlib
ROOT=Path(__file__).resolve().parents[1]

def main():
    run='nsai-implementation-'+uuid4().hex[:12]
    net,db,worker=run+'-net',run+'-db',run+'-worker'
    made=[];checks=[];report=dict(run_id=run,status='FAIL',user_volumes_accessed=False,host_ports_published=False)
    def command(args,**kwargs):
        if isinstance(kwargs.get('input'),str):kwargs['input']=kwargs['input'].encode('utf-8')
        result=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=kwargs.pop('timeout',120),**kwargs)
        result.stdout=result.stdout.decode('utf-8');result.stderr=result.stderr.decode('utf-8',errors='replace')
        if result.returncode:
            report['owned_failure_diagnostics']=(result.stdout+result.stderr)[-6000:].replace('synthetic-test-only-'+'x'*48,'[synthetic credential]')
            raise RuntimeError('Owned command failed: '+args[0]+' '+args[1]+'; diagnostics in private receipt')
        return result.stdout
    try:
        image=command(['docker','image','inspect','nsai-implementation-candidate:local','--format','{{.Id}}']).strip()
        db_image=command(['docker','image','inspect','amd-hackathon-nsai-db:local','--format','{{.Id}}']).strip()
        report.update(image=image,db_image=db_image)
        command(['docker','network','create','--internal','--label','nsai.owner=implementation',net]);made.append(('network',net))
        command(['docker','run','-d','--rm','--name',db,'--label','nsai.owner=implementation','--network',net,'--memory','1g','--cpus','1','--pids-limit','128','--security-opt','no-new-privileges:true','--tmpfs','/var/lib/postgresql/data:rw,nosuid,nodev,size=512m','--tmpfs','/var/run/postgresql:rw,nosuid,nodev,size=8m','-e','POSTGRES_USER=nsai','-e','POSTGRES_DB=nsai','-e','POSTGRES_PASSWORD=synthetic-test-only-'+'x'*48,db_image]);made.append(('container',db))
        for _ in range(30):
            if subprocess.run(['docker','exec',db,'pg_isready','-U','nsai','-d','nsai'],capture_output=True,timeout=5).returncode==0:break
            time.sleep(1)
        else:raise RuntimeError('Owned database readiness failed')
        spec=importlib.util.spec_from_file_location('migration_helper',ROOT/'scripts/migrate.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        sql=module.migration_sql(ROOT)+module.role_sql('synthetic-test-only-'+'x'*48)
        command(['docker','exec','-i',db,'psql','-v','ON_ERROR_STOP=1','-U','nsai','-d','nsai'],input=sql)
        command(['docker','exec','-i',db,'psql','-v','ON_ERROR_STOP=1','-U','nsai','-d','nsai'],input=module.migration_sql(ROOT)+'COMMIT;')
        report['migration_repeat']='PASS'
        harness=(ROOT/'scripts/implementation_integration_harness.py').read_text(encoding='utf-8')
        report['harness_sha256']=hashlib.sha256(harness.encode()).hexdigest()
        prefix="from pathlib import Path\np=Path('/tmp/db-password');p.write_text('synthetic-test-only-'+'x'*48)\n"
        output=command(['docker','run','--rm','-i','--name',worker,'--label','nsai.owner=implementation','--network',net,'--read-only','--cap-drop','ALL','--security-opt','no-new-privileges:true','--user','10001:10001','--memory','768m','--cpus','2','--pids-limit','64','--tmpfs','/tmp:rw,nosuid,nodev,noexec,size=32m','-e','NSAI_DB_HOST='+db,'-e','NSAI_DB_NAME=nsai','-e','NSAI_DB_USER=nsai_app','-e','NSAI_DB_PASSWORD_FILE=/tmp/db-password',image,'python','-'],input=prefix+harness,timeout=180)
        report.update(json.loads(output))
    except Exception as error:report.update(status='FAIL',error_type=type(error).__name__,error=str(error) if isinstance(error,RuntimeError) else 'Owned qualification failure; detailed diagnostics withheld')
    finally:
        cleanup=[]
        # Every name is generated in this function and bound to this owned run.
        for name in [worker,db]:
            result=subprocess.run(['docker','rm','-f',name],capture_output=True,timeout=20)
            cleanup.append(dict(resource=name,removed=result.returncode==0,already_absent=result.returncode!=0))
        if ('network',net) in made:
            result=subprocess.run(['docker','network','rm',net],capture_output=True,timeout=20)
            cleanup.append(dict(resource=net,removed=result.returncode==0))
        report.update(cleanup=cleanup,captured_at=datetime.now(timezone.utc).isoformat())
        dest=ROOT/'evidence/implementation';dest.mkdir(exist_ok=True)
        path=dest/(run+'.json');path.write_text(json.dumps(report,indent=2),encoding='utf-8')
        (dest/'integration-current.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
    return 0 if report['status']=='PASS_SCOPED' else 1

if __name__=='__main__':raise SystemExit(main())
