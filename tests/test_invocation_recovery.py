from contextlib import contextmanager
import pytest
from nsai import workflow_store as workflows
from nsai.contracts.evidence import canonical_hash


@pytest.mark.parametrize('response',[None,[],{'mode':'model_unverified','answer':'Obsolete claim'},
    {'mode':'model_unverified','support_policy_version':'nsai.answer-support/1','answer':'75 C'}, {'mode':'unknown'}])
def test_obsolete_completed_response_cannot_reexecute_or_replay(monkeypatch,response):
    payload={'question':'limit?'};commands=[]
    class Result:
        def fetchone(self):return (canonical_hash(payload),'completed',response,False)
    class Connection:
        def execute(self,sql,args=None):commands.append(sql);return Result()
    @contextmanager
    def connect():yield Connection()
    monkeypatch.setattr(workflows.store,'connect',connect)
    with pytest.raises(ValueError,match='current support validation'):
        workflows.begin_invocation('owner','a'*32,payload)
    assert not any(sql.startswith(('INSERT','UPDATE')) for sql in commands)


def test_current_completion_replays_exactly_without_mutation(monkeypatch):
    from nsai.answer_support import VERSION
    payload={'question':'limit?'}
    response={'mode':'model_unverified','support_policy_version':VERSION,'answer':'75 C'}
    commands=[]
    class Result:
        def fetchone(self):return (canonical_hash(payload),'completed',response,False)
    class Connection:
        def execute(self,sql,args=None):commands.append(sql);return Result()
    @contextmanager
    def connect():yield Connection()
    monkeypatch.setattr(workflows.store,'connect',connect)
    assert workflows.begin_invocation('owner','a'*32,payload) is response
    assert not any(sql.startswith(('INSERT','UPDATE')) for sql in commands)


def test_old_completion_status_retains_state_but_withholds_answer(monkeypatch):
    class Connection:
        def execute(self,*args):return None
    @contextmanager
    def connect():yield Connection()
    monkeypatch.setattr(workflows.store,'connect',connect)
    monkeypatch.setattr(workflows,'rows',lambda _: [dict(request_id='a'*32,state='completed',response={'mode':'model_unverified','answer':'old'},created_at='retained')])
    result=workflows.invocation_status('owner','a'*32)
    assert result['state']=='completed' and result['created_at']=='retained'
    assert result['response'] is None and result['response_withheld']

def test_expired_pending_invocation_commits_failure_without_reexecution(monkeypatch):
    payload={'question':'What is the limit?'}
    commands=[]
    class Result:
        def fetchone(self):return (canonical_hash(payload),'pending',None,True)
    class Connection:
        def execute(self,sql,args=None):commands.append((sql,args));return Result()
        def commit(self):commands.append(('COMMIT',None))
    @contextmanager
    def connect():yield Connection()
    monkeypatch.setattr(workflows.store,'connect',connect)
    with pytest.raises(ValueError,match='pending or failed'):
        workflows.begin_invocation('owner','a'*32,payload)
    assert any("state='failed'" in sql for sql,_ in commands)
    assert commands[-1][0]=='COMMIT'
    assert not any('INSERT' in sql for sql,_ in commands)

@pytest.mark.parametrize('data',[b'x'*2048,b'x'*31,b'x'*32+b' bad',b'\xff'*40])
def test_database_credentials_are_bounded_and_validated(tmp_path,data):
    from nsai.store import _secret
    path=tmp_path/'credential';path.write_bytes(data)
    with pytest.raises((RuntimeError,UnicodeError)):_secret(str(path))
