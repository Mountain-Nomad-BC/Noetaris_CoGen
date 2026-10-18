from types import SimpleNamespace
from nsai import store


def test_atomic_replacement_invalidates_cache_even_when_timestamps_and_size_alias(monkeypatch):
    state=dict(value='A'*43,inode=100,reads=0)
    class Source:
        def __init__(self,path):pass
        def resolve(self):return 'owned-synthetic-credential'
        def stat(self):return SimpleNamespace(st_size=44,st_mtime_ns=1,st_ctime_ns=1,st_ino=state['inode'],st_dev=1)
        def read_text(self,encoding):state['reads']+=1;return state['value']+'\n'
    monkeypatch.setattr(store,'Path',Source);monkeypatch.setattr(store,'_secret_cache',{})
    assert store._secret('owned-synthetic')=='A'*43
    assert store._secret('owned-synthetic')=='A'*43 and state['reads']==1
    state.update(value='B'*43,inode=101)
    assert store._secret('owned-synthetic')=='B'*43 and state['reads']==2
