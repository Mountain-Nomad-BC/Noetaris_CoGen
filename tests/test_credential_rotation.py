"""Original stopped-dependency credential exchange and rollback contracts."""
from pathlib import Path
import sys
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import rotate_local_credentials as rotation
OLD='A'*43
NEW='B'*43

def fixture(tmp_path):
    secret=tmp_path/'role.txt';secret.write_bytes((OLD+'\n').encode());state={'password':OLD,'quiescent_checks':0}
    def set_password(value):state['password']=value
    def verify(value):
        if value!=state['password']:raise ValueError('Login denied')
    def quiescent():state['quiescent_checks']+=1
    arguments=dict(secret_path=secret,new_secret=NEW,set_database_password=set_password,verify_login=verify,ensure_quiescent=quiescent,read_secret=lambda:rotation.bounded_secret(secret,tmp_path))
    return secret,state,arguments

def test_success_updates_single_lf_line_and_fingerprint(tmp_path):
    secret,state,args=fixture(tmp_path);report=rotation.rotate_transaction(**args)
    assert state['password']==NEW and secret.read_bytes()==(NEW+'\n').encode()
    assert report['pool_fingerprint_changed'] and report['phases'][-1]=='settled'
    assert state['quiescent_checks']==2

@pytest.mark.parametrize('phase',['database-changed','replacement-login-verified','file-replaced','settled'])
def test_every_postmutation_failure_restores_database_and_file(tmp_path,phase):
    secret,state,args=fixture(tmp_path)
    def fail(name):
        if name==phase:raise RuntimeError('Synthetic injected failure')
    with pytest.raises(RuntimeError):rotation.rotate_transaction(**args,phase=fail)
    assert state['password']==OLD and secret.read_bytes()==(OLD+'\n').encode()

def test_cancel_and_uncertain_commit_compensated(tmp_path):
    secret,state,args=fixture(tmp_path)
    def cancel(name):
        if name=='database-changed':raise KeyboardInterrupt()
    with pytest.raises(KeyboardInterrupt):rotation.rotate_transaction(**args,phase=cancel)
    assert state['password']==OLD and secret.read_bytes()==(OLD+'\n').encode()
    original=args['set_database_password']
    def uncertain(value):
        original(value)
        if value==NEW:raise ConnectionError('Commit result unavailable')
    args['set_database_password']=uncertain
    with pytest.raises(ConnectionError):rotation.rotate_transaction(**args)
    assert state['password']==OLD

def test_recovery_failure_never_reports_settled(tmp_path):
    secret,state,args=fixture(tmp_path)
    def setter(value):
        if value==OLD:raise ConnectionError('Synthetic rollback failure')
        state['password']=value
    args['set_database_password']=setter
    def fail(name):
        if name=='database-changed':raise RuntimeError('Synthetic failure')
    with pytest.raises(rotation.RotationRecoveryError):rotation.rotate_transaction(**args,phase=fail)
    assert state['password']==NEW

@pytest.mark.parametrize('value',['short','A'*31,'A'*257,'A'*32+'\n','A'*32+'\r','A'*32+'\u00e9',"A'*32;"])
def test_invalid_credentials_rejected_without_mutation(tmp_path,value):
    secret,state,args=fixture(tmp_path);args['new_secret']=value
    with pytest.raises(ValueError):rotation.rotate_transaction(**args)
    assert state['password']==OLD and secret.read_bytes()==(OLD+'\n').encode()

def test_running_dependencies_and_production_default_rejected(tmp_path):
    secret,state,args=fixture(tmp_path)
    def deny():raise ValueError('Dependent running')
    args['ensure_quiescent']=deny
    with pytest.raises(ValueError):rotation.rotate_transaction(**args)
    assert state['password']==OLD
    for name in ['amd-hackathon-nsai-db-1','','postgres']:
        with pytest.raises(ValueError):rotation.owned_target(name)

def test_secret_workspace_and_line_rules(tmp_path):
    outside=tmp_path/'outside.txt';outside.write_text(OLD)
    with pytest.raises(ValueError):rotation.bounded_secret(outside,tmp_path/'owned')
    outside.write_bytes((OLD+'\r\n').encode())
    with pytest.raises(ValueError):rotation.bounded_secret(outside,tmp_path)


def test_dotdot_secret_escape_rejected(tmp_path):
    owned=tmp_path/'owned';owned.mkdir();outside=tmp_path/'outside.txt';outside.write_text(OLD)
    with pytest.raises(ValueError):rotation.bounded_secret(owned/'..'/'outside.txt',owned)
