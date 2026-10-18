"""Release-guarded one-time legacy index preparation in a uniquely owned client."""
from pathlib import Path
import argparse
import json
import subprocess
import sys
from uuid import uuid4
from verify_recovery import cleanup_owned

ROOT=Path(__file__).resolve().parents[1]


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--limit',type=int,default=100)
    args=parser.parse_args(argv)
    if not 1<=args.limit<=1000:parser.error('Limit must be between 1 and 1000')
    gate=subprocess.run([sys.executable,str(ROOT/'scripts/check_release_readiness.py')],cwd=ROOT,timeout=120)
    if gate.returncode:
        raise SystemExit('Legacy preparation denied: independent release admission is incomplete. No source or index changes were made.')
    owner=uuid4().hex;name='nsai-legacy-preparation-'+owner
    command=['docker','compose','-f','compose.yaml','-f','deploy/local/compose.cpu.yaml','-f','deploy/local/compose.semantic.yaml',
        'run','--rm','--no-deps','-T','--name',name,'--label','nsai.owner='+owner,'--entrypoint','python','api',
        '-m','nsai.legacy_library_backfill','--limit',str(args.limit)]
    try:
        result=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=900)
        if result.returncode:return 1
        report=json.loads(result.stdout.strip().splitlines()[-1])
        if report.get('status')!='QUEUED' or report.get('publication_accepted') is not False:return 1
        print(json.dumps(report));return 0
    finally:
        if not cleanup_owned(name,owner):raise RuntimeError('Owned legacy preparation client cleanup requires review')


if __name__=='__main__':raise SystemExit(main())
