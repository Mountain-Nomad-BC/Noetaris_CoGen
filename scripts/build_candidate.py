"""Retain the exact prior candidate before an explicitly requested candidate build."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
ALIAS='nsai-implementation-candidate:local'

def invoke(arguments):
    return subprocess.run(['docker',*arguments],cwd=ROOT,capture_output=True,timeout=1800)

def resolve(reference,run=invoke):
    result=run(['image','inspect','--format','{{.Id}}',reference])
    if result.returncode:
        raise RuntimeError('Image identity unavailable')
    value=result.stdout.decode().strip()
    if not re.fullmatch(r'sha256:[a-f0-9]{64}',value):
        raise RuntimeError('Invalid image identity')
    return value

def retain(run=invoke):
    previous=resolve(ALIAS,run)
    hold='nsai-candidate-hold:'+previous.removeprefix('sha256:')
    existing=run(['image','inspect','--format','{{.Id}}',hold])
    if existing.returncode==0:
        if existing.stdout.decode().strip()!=previous:
            raise RuntimeError('Hold tag collision')
    else:
        tagged=run(['image','tag',previous,hold])
        if tagged.returncode:
            raise RuntimeError('Candidate retention failed')
    if resolve(hold,run)!=previous:
        raise RuntimeError('Candidate retention verification failed')
    return previous,hold

def snapshot(root):
    import stat
    def reject_link(path):
        info=path.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0)&getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',1024):
            raise RuntimeError('Source links or junctions are not admitted')
    def walk(directory):
        try:reject_link(directory)
        except FileNotFoundError:return
        for path in directory.iterdir():
            if path.name=='__pycache__' or path.suffix=='.pyc':continue
            reject_link(path)
            if path.is_dir():yield from walk(path)
            elif path.is_file():yield path
    for name in ('requirements.lock','requirements-build.lock','Dockerfile','.dockerignore'):
        reject_link(root/name)
        if not (root/name).is_file():
            raise RuntimeError('Required locked build input missing')
    result={}
    for directory in ('src','assets','database','deploy','scripts','LICENSES'):
        for path in walk(root/directory):
            result[path.relative_to(root).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
    for pattern in ('Dockerfile*','compose*.yaml','requirements*.lock','pyproject.toml','.dockerignore','LICENSE','NOTICE'):
        for path in root.glob(pattern):
            reject_link(path)
            result[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
    return result

def perform(*,build=False,run=invoke,root=ROOT):
    report=dict(run_id=uuid4().hex,captured_at=datetime.now(timezone.utc).isoformat(),status='FAIL',build_requested=build,live_alias_changed=False)
    try:
        before=snapshot(root)
        report['source_manifest']=before
        previous,hold=retain(run)
        report.update(previous_image=previous,hold_tag=hold,retention_verified=True)
        if build:
            # Stage into a unique candidate tag first; failed builds never replace the alias.
            staged='nsai-candidate-stage:'+report['run_id']
            built=run(['build','--pull=false','--tag',staged,'.'])
            report['build_exit_code']=built.returncode
            # Only bounded digest metadata is persisted, never raw logs or environment.
            report['private_build_output_sha256']=hashlib.sha256(built.stdout+built.stderr).hexdigest()
            if built.returncode:raise RuntimeError('Candidate build failed; prior image retained')
            if snapshot(root)!=before:raise RuntimeError('Build source changed; candidate alias not updated')
            candidate=resolve(staged,run)
            if resolve(ALIAS,run)!=previous:raise RuntimeError('Candidate alias changed concurrently')
            tagged=run(['image','tag',candidate,ALIAS])
            if tagged.returncode or resolve(ALIAS,run)!=candidate:raise RuntimeError('Candidate promotion failed')
            report['candidate_image']=candidate
        if snapshot(root)!=before:raise RuntimeError('Source changed during candidate operation')
        report['status']='PASS'
    except (RuntimeError,OSError,ValueError,UnicodeError,subprocess.SubprocessError) as error:
        report['failure_type']=type(error).__name__
        safe_reasons={'Hold tag collision':'HOLD_COLLISION','Candidate retention failed':'HOLD_FAILED',
            'Candidate retention verification failed':'HOLD_VERIFICATION_FAILED','Image identity unavailable':'IMAGE_UNAVAILABLE',
            'Invalid image identity':'INVALID_IMAGE_ID','Required locked build input missing':'LOCKFILE_MISSING',
            'Source links or junctions are not admitted':'SOURCE_REPARSE_POINT',
            'Candidate build failed; prior image retained':'BUILD_FAILED','Build source changed; candidate alias not updated':'SOURCE_CHANGED',
            'Candidate alias changed concurrently':'ALIAS_CHANGED','Candidate promotion failed':'PROMOTION_FAILED',
            'Source changed during candidate operation':'SOURCE_CHANGED'}
        report['failure_reason']=safe_reasons.get(str(error),'OPERATION_FAILED') if type(error) is RuntimeError else 'OPERATION_FAILED'
    return report

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    action=parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--build',action='store_true')
    action.add_argument('--retain-only',action='store_true')
    args=parser.parse_args(argv)
    report=perform(build=args.build)
    destination=ROOT/'evidence/implementation/candidate-builds'/report['run_id']
    destination.mkdir(parents=True,exist_ok=False)
    (destination/'receipt.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
    return 0 if report['status']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
