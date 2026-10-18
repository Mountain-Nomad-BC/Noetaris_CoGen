"""Request authority follows async/thread boundaries and never pool reuse."""
import asyncio
from queue import LifoQueue
from threading import BoundedSemaphore

import pytest
from nsai import store, security


def identity(actor='alice', role='operator'):
    return dict(actor='local-user-'+actor,role=role,identity_kind='local-user',
                permissions=sorted(security.ROLES[role]))


def test_nested_context_restores_identity_even_after_failure():
    assert store.request_identity() is None
    with store.identity_context(identity()):
        assert store.request_identity()['actor']=='local-user-alice'
        with pytest.raises(RuntimeError):
            with store.identity_context(identity('bob')):
                assert store.request_identity()['actor']=='local-user-bob'
                raise RuntimeError('owned failure')
        assert store.request_identity()['actor']=='local-user-alice'
    assert store.request_identity() is None


def test_concurrent_requests_and_thread_work_keep_distinct_authority():
    async def run():
        async def request(name):
            with store.identity_context(identity(name)):
                await asyncio.sleep(0)
                return await asyncio.to_thread(store.request_identity)
        return await asyncio.gather(request('alice'),request('bob'))
    assert [r['actor'] for r in asyncio.run(run())]==['local-user-alice','local-user-bob']
    assert store.request_identity() is None


@pytest.mark.parametrize('bad',[dict(actor='local-user-ALICE',role='operator'),
                                 dict(actor='local-user-alice',role='root'),
                                 dict(actor='client-selected-agent',role='admin')])
def test_invalid_server_identity_never_enters_context(bad):
    with pytest.raises(ValueError):
        with store.identity_context(bad):pytest.fail('Invalid context admitted')
    assert store.request_identity() is None


def test_authentication_dependencies_use_the_already_verified_identity(monkeypatch):
    with store.identity_context(identity()):
        monkeypatch.setattr(security,'_local_identities',lambda:pytest.fail('Identity resolved twice'))
        assert security.principal(None)==identity()


def test_every_pool_lease_binds_context_and_failure_rolls_back(monkeypatch):
    import psycopg
    from nsai import schema_contract
    monkeypatch.setattr(schema_contract,'verify_database_contract',lambda conn:None)
    class Connection:
        closed=False
        def __init__(self):self.events=[]
        def execute(self,sql,args=None):self.events.append((sql,args));return self
        def fetchall(self):return []
        def commit(self):self.events.append(('commit',None))
        def rollback(self):self.events.append(('rollback',None))
    conn=Connection()
    monkeypatch.setattr(psycopg,'connect',lambda **kw:conn)
    monkeypatch.setattr(store,'_secret',lambda path:'synthetic-test-password-'+'x'*32)
    monkeypatch.setenv('NSAI_DB_PASSWORD_FILE','unused-owned-test-path')
    monkeypatch.setattr(store,'_idle',LifoQueue(maxsize=4))
    monkeypatch.setattr(store,'_slots',BoundedSemaphore(4))
    with store.identity_context(identity()):
        with store.connect() as first:assert first is conn
    monkeypatch.setenv('NSAI_CAPACITY_PROFILE','reference-1000')
    with pytest.raises(RuntimeError):
        with store.identity_context(identity('bob')):
            with store.connect() as second:
                assert second is conn
                raise RuntimeError('owned rollback')
    monkeypatch.delenv('NSAI_CAPACITY_PROFILE',raising=False)
    with store.connect() as third:assert third is conn
    bindings=[args for sql,args in conn.events if 'set_config' in sql]
    assert bindings==[('local-user-alice','operator','','','default'),('local-user-bob','operator','','','reference-1000'),('legacy-service','service','','','default')]
    assert [sql for sql,args in conn.events if sql in {'commit','rollback'}]==['commit','rollback','commit']
