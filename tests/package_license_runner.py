"""Compare packaged root notices/license bytes; no legal clearance is asserted."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]


def main():
    run=uuid4().hex;folder=ROOT/'evidence/package-license-delivery'/run;folder.mkdir(parents=True)
    files=['LICENSE','NOTICE',*[path.relative_to(ROOT).as_posix() for path in sorted((ROOT/'LICENSES').rglob('*')) if path.is_file()]]
    expected={path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in files}
    report=dict(status='FAIL',run_id=run,scope=__doc__,recorded_at=datetime.now(timezone.utc).isoformat(),
        expected=expected,images={},material_rights_accepted=False,live_services_accessed=False,cleanup=[])
    try:
        for component,alias,prefix,user in [('api','nsai-implementation-candidate:local','/app','10001:10001'),
            ('encoder','nsai-cpu-encoder:qualification','/app','10001:10001'),
            ('ocr','nsai-ocr-hardened-candidate:local','/opt/app','10002:10002')]:
            identity=subprocess.run(['docker','image','inspect',alias,'--format','{{.Id}}'],capture_output=True,check=True,timeout=30).stdout.decode().strip()
            name='nsai-notice-'+uuid4().hex
            try:
                program="import hashlib,json;from pathlib import Path;print(json.dumps({p:hashlib.sha256((Path("+repr(prefix)+")/p).read_bytes()).hexdigest() for p in "+repr(files)+"}))"
                result=subprocess.run(['docker','run','--rm','--name',name,'--label','nsai.owner='+run,
                    '--network','none','--read-only','--user',user,'--cap-drop','ALL','--security-opt','no-new-privileges:true',
                    '--cpus','.25','--memory','128m','--pids-limit','32','--entrypoint','python',identity,'-c',program],
                    capture_output=True,timeout=30)
                assert result.returncode==0,'Packaged notice read failed'
                actual=json.loads(result.stdout)
                assert actual==expected,'Packaged notices differ from reviewed source bytes'
                report['images'][component]=dict(image=identity,actual=actual,byte_match=True)
            finally:
                found=subprocess.run(['docker','inspect',name],capture_output=True,timeout=30)
                removed=found.returncode!=0
                if not removed:
                    assert json.loads(found.stdout)[0]['Config'].get('Labels',{}).get('nsai.owner')==run
                    removed=subprocess.run(['docker','rm','--force',name],capture_output=True,timeout=30).returncode==0
                report['cleanup'].append(dict(name=name,removed=removed))
        report['status']='PASS_BYTES_ONLY'
    except Exception as error:
        report['failure_type']=type(error).__name__;report['failure']=str(error)[:500]
    finally:
        after={path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in files}
        report['source_bytes_unchanged']=after==expected
        if not report['source_bytes_unchanged'] or not all(item['removed'] for item in report['cleanup']):report['status']='FAIL'
        (folder/'receipt.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=report['status'],run_id=run,material_rights_accepted=False)))
    return 0 if report['status']=='PASS_BYTES_ONLY' else 1


if __name__=='__main__':raise SystemExit(main())
