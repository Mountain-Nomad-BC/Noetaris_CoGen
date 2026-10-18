import importlib.util
from pathlib import Path
from types import SimpleNamespace
import pytest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('candidate_retention',ROOT/'scripts/build_candidate.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
OLD='sha256:'+'a'*64
NEW='sha256:'+'b'*64

class Docker:
    def __init__(self,collision=False,tag_failure=False,build_failure=False):
        self.images={module.ALIAS:OLD};self.calls=[]
        if collision:self.images['nsai-candidate-hold:'+'a'*64]=NEW
        self.tag_failure=tag_failure;self.build_failure=build_failure
    def __call__(self,args):
        self.calls.append(args)
        code=0;out=b''
        if args[:2]==['image','inspect']:
            value=self.images.get(args[-1]);code=0 if value else 1;out=(value or '').encode()
        elif args[:2]==['image','tag']:
            code=1 if self.tag_failure else 0
            if not code:self.images[args[3]]=args[2]
        elif args[0]=='build':
            code=1 if self.build_failure else 0
            if not code:self.images[args[args.index('--tag')+1]]=NEW
        else:pytest.fail('Unexpected Docker command')
        return SimpleNamespace(returncode=code,stdout=out,stderr=b'')

@pytest.fixture
def root(tmp_path):
    for name in ('requirements.lock','requirements-build.lock','Dockerfile','.dockerignore'):
        (tmp_path/name).write_text('synthetic locked input')
    return tmp_path

def test_hold_precedes_build_and_promotion(root):
    docker=Docker();report=module.perform(build=True,run=docker,root=root)
    assert report['status']=='PASS'
    hold=next(i for i,c in enumerate(docker.calls) if c[:2]==['image','tag'])
    build=next(i for i,c in enumerate(docker.calls) if c[0]=='build')
    assert hold<build and docker.images['nsai-candidate-hold:'+'a'*64]==OLD
    assert docker.images[module.ALIAS]==NEW

@pytest.mark.parametrize('configuration',[dict(collision=True),dict(tag_failure=True)])
def test_hold_failure_prevents_build(root,configuration):
    docker=Docker(**configuration)
    assert module.perform(build=True,run=docker,root=root)['status']=='FAIL'
    assert not any(c[0]=='build' for c in docker.calls)

def test_failed_build_retains_previous_alias_and_hold(root):
    docker=Docker(build_failure=True);report=module.perform(build=True,run=docker,root=root)
    assert report['status']=='FAIL' and report['build_exit_code']==1
    assert report['failure_reason']=='BUILD_FAILED'
    assert docker.images[module.ALIAS]==OLD and docker.images[report['hold_tag']]==OLD

def test_retain_only_never_builds(root):
    docker=Docker();assert module.perform(run=docker,root=root)['status']=='PASS'
    assert not any(c[0]=='build' for c in docker.calls)

def test_missing_lock_prevents_docker(root):
    (root/'requirements.lock').unlink()
    docker=Docker();assert module.perform(build=True,run=docker,root=root)['status']=='FAIL'
    assert docker.calls==[]

def test_source_drift_prevents_alias_promotion(root):
    docker=Docker()
    def run(args):
        result=docker(args)
        if args[0]=='build':(root/'Dockerfile').write_text('changed')
        return result
    assert module.perform(build=True,run=run,root=root)['status']=='FAIL'
    assert docker.images[module.ALIAS]==OLD


@pytest.mark.parametrize('path',['NOTICE','LICENSES/component.txt'])
def test_notice_or_license_drift_prevents_alias_promotion(root,path):
    target=root/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_text('original terms')
    docker=Docker()
    def run(args):
        result=docker(args)
        if args[0]=='build':target.write_text('changed terms')
        return result
    assert module.perform(build=True,run=run,root=root)['status']=='FAIL'
    assert docker.images[module.ALIAS]==OLD

def test_import_is_pure_and_cli_requires_explicit_action(monkeypatch):
    monkeypatch.setattr(module.subprocess,'run',lambda *a,**k:pytest.fail('Import touched Docker'))
    spec.loader.exec_module(module)
    with pytest.raises(SystemExit) as result:module.main([])
    assert result.value.code==2

def test_failed_build_cli_nonzero(monkeypatch,tmp_path):
    monkeypatch.setattr(module,'ROOT',tmp_path)
    monkeypatch.setattr(module,'perform',lambda **kwargs:dict(run_id='synthetic-run',status='FAIL'))
    assert module.main(['--build'])==1

@pytest.mark.parametrize('target',['src','requirements.lock','Dockerfile.extra'])
def test_reparse_boundary_refuses_descent_and_reads(root,monkeypatch,target):
    import stat
    path=root/target
    if target=='src':path.mkdir()
    elif not path.exists():path.write_text('synthetic')
    original=Path.lstat
    def lstat(self,*args,**kwargs):
        value=original(self,*args,**kwargs)
        if self==path:
            return SimpleNamespace(st_mode=value.st_mode,st_file_attributes=getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',1024))
        return value
    original_read=Path.read_bytes
    original_iter=Path.iterdir
    def read(self):
        assert self!=path,'Reparse file read before rejection'
        return original_read(self)
    def iterate(self):
        assert self!=path,'Reparse directory descended before rejection'
        return original_iter(self)
    monkeypatch.setattr(Path,'lstat',lstat)
    monkeypatch.setattr(Path,'read_bytes',read)
    monkeypatch.setattr(Path,'iterdir',iterate)
    with pytest.raises(RuntimeError,match='junction'):
        module.snapshot(root)

def test_raw_docker_stderr_never_in_failure_report(root):
    docker=Docker(build_failure=True)
    def run(args):
        result=docker(args)
        if args[0]=='build':result.stderr=b'private-key-and-host-path-secret'
        return result
    import json
    report=module.perform(build=True,run=run,root=root)
    assert report['failure_reason']=='BUILD_FAILED'
    assert 'private-key' not in json.dumps(report)
