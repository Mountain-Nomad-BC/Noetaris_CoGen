"""Frozen-source full regression on bounded, owned disposable databases.

Uses existing immutable integration image identities; never rebuilds or restarts
the running application. All skips, missing cases and cleanup failures fail.
"""
from datetime import datetime,timezone
import json
import os
import platform
import re
import subprocess
import sys
from uuid import uuid4

from start_integration import ROOT,STATE
from check_deployment_stages import regression_snapshot
from qualification_shards import execute,cleanup_owned


def main():
    identity=json.loads((STATE/'identity.json').read_text())
    if identity.get('project')!='noetaris-integration':
        raise RuntimeError('Owned integration identity required')
    images={key:identity['images'][key] for key in ('api','db')}
    for value in images.values():
        if not isinstance(value,str) or not re.fullmatch(r'sha256:[0-9a-f]{64}',value):
            raise RuntimeError('Exact local image identities required')
        result=subprocess.run(['docker','image','inspect','--format','{{.Id}}',value],
                              capture_output=True,timeout=30)
        if result.returncode or result.stdout.decode().strip()!=value:
            raise RuntimeError('Required immutable image is unavailable')
    # NumPy is needed by the encoder window test, even on the host runner.
    import numpy
    owner=uuid4().hex
    folder=ROOT/'evidence/integration-deployment'/('qualification-'+owner)
    folder.mkdir(parents=True)
    receipt=dict(run_id=owner,status='INCOMPLETE_OR_FAILED',
        captured_at=datetime.now(timezone.utc).isoformat(),
        scope='Full frozen-source regression with owned DB fixtures; not independent release acceptance',
        api_image=images['api'],db_image=images['db'],python=platform.python_version(),
        numpy=numpy.__version__,source_before=regression_snapshot(ROOT))
    environment=os.environ.copy()
    environment.update(NSAI_TEST_PRIVATE_DATABASE='1',NSAI_TEST_PRIVATE_OWNER=owner,
        NSAI_TEST_PRIVATE_DATABASE_IMAGE=images['db'],NSAI_TEST_PRIVATE_APPLICATION_IMAGE=images['api'],
        NSAI_TEST_PRIVATE_PACKAGED_SOURCE='1')
    try:
        receipt['result']=execute(ROOT,folder,environment)
        actual=json.loads((folder/'coverage.json').read_text())
        receipt.update(counts=actual['counts'],coverage_exact=actual['exact'],
            source_unchanged=regression_snapshot(ROOT)==receipt['source_before'])
        if receipt['result']['exit_code']==0 and receipt['source_unchanged']:
            receipt['status']='PASS_SCOPED'
    except Exception as error:
        # Do not emit inherited environment, source records or command output.
        receipt['failure_type']=type(error).__name__
    finally:
        try:receipt['cleanup']=cleanup_owned(owner)
        except Exception as error:
            receipt['cleanup']=dict(complete=False,failure_type=type(error).__name__)
            receipt['status']='INCOMPLETE_OR_FAILED'
        (folder/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:receipt.get(key) for key in
        ('run_id','status','counts','coverage_exact','source_unchanged','cleanup')},indent=2))
    print(str(folder/'receipt.json'))
    return 0 if receipt['status']=='PASS_SCOPED' else 1


if __name__=='__main__':raise SystemExit(main())
