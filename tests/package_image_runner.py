"""Retain exact-image SBOM/advisories; never substitute for canonical code review."""
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from check_release_readiness import source_snapshot


def main(component=None):
    run=uuid4().hex;folder=ROOT/'evidence/package-risk'/run;folder.mkdir(parents=True)
    report=dict(status='FAIL',run_id=run,scope=__doc__,recorded_at=datetime.now(timezone.utc).isoformat(),
        source_before=source_snapshot(ROOT),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        live_containers_accessed=False,release_approved=False,canonical_security_scan=False,images={})
    aliases={'api_parser':'nsai-implementation-candidate:local','database':'nsai-db-package-qualified:local',
        'encoder':'nsai-cpu-encoder:qualification','ocr':'nsai-ocr-hardened-candidate:local',
        'cpu_model_server':'sha256:89f180f16f295ee496fe00924ec2118cae2efec519d1a82c605420af09d2a6df'}
    if component is not None:aliases={component:aliases[component]}
    try:
        version=subprocess.run(['docker','scout','version'],capture_output=True,timeout=30)
        assert version.returncode==0,'Docker Scout unavailable'
        (folder/'scout-version.txt').write_bytes(version.stdout+version.stderr)
        pinned={}
        for component,alias in aliases.items():
            found=subprocess.run(['docker','image','inspect',alias,'--format','{{.Id}}'],capture_output=True,timeout=30,check=True)
            identity=found.stdout.decode().strip();assert re.fullmatch('sha256:[a-f0-9]{64}',identity)
            pinned[component]=identity
        report['pinned_images']=pinned
        for component,identity in pinned.items():
            destination=folder/component;destination.mkdir()
            item=dict(image=identity,commands=[],severity_counts={},findings=[]);report['images'][component]=item
            commands=[('sbom',['docker','scout','sbom','--format','spdx','--output',str(destination/'image.spdx.json'),'local://'+identity]),
                ('cves',['docker','scout','cves','--exit-code','--format','sarif','--output',str(destination/'vulnerabilities.sarif.json'),'sbom://'+str(destination/'image.spdx.json')])]
            for label,args in commands:
                result=subprocess.run(args,capture_output=True,timeout=600)
                (destination/(label+'-stdout.txt')).write_bytes(result.stdout)
                (destination/(label+'-stderr.txt')).write_bytes(result.stderr)
                item['commands'].append(dict(name=label,argv=args,exit_code=result.returncode))
                assert result.returncode in ({0} if label=='sbom' else {0,2}),'Package advisory command failed'
            sarif=json.loads((destination/'vulnerabilities.sarif.json').read_text(encoding='utf-8'))
            for scan in sarif.get('runs',[]):
                rules={rule['id']:rule for rule in scan['tool']['driver'].get('rules',[])}
                for finding in scan.get('results',[]):
                    rule=rules[finding['ruleId']];properties=rule.get('properties',{})
                    item['findings'].append(dict(id=finding['ruleId'],severity=properties.get('cvssV3_severity','UNKNOWN'),
                        packages=properties.get('purls',[]),fixed_version=properties.get('fixed_version'),
                        reference=rule.get('helpUri'),validation='NOT_TRIAGED'))
            item['severity_counts']=dict(Counter(finding['severity'] for finding in item['findings']))
            item['status']='RAW_RESULTS_RETAINED'
            item['artifacts']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in destination.iterdir() if p.is_file()}
            print(json.dumps(dict(progress=component,image=identity,severity_counts=item['severity_counts'])),flush=True)
        report['status']='COMPLETE_RAW_PACKAGE_RESULTS'
    except Exception as error:
        report['failure_type']=type(error).__name__;report['failure']=str(error)[:500]
    finally:
        report['source_after']=source_snapshot(ROOT)
        if report['source_before']!=report['source_after']:report['status']='FAIL'
        report['completed_at']=datetime.now(timezone.utc).isoformat()
        (folder/'package-receipt.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=report['status'],run_id=run,release_approved=False)))
    return 0 if report['status']=='COMPLETE_RAW_PACKAGE_RESULTS' else 1


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--component',choices=['api_parser','database','encoder','ocr','cpu_model_server'])
    raise SystemExit(main(parser.parse_args().component))
