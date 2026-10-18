import asyncio
from threading import Event
import pytest


def test_cancelled_admission_waits_for_inflight_commit_before_release(monkeypatch):
    from nsai import operation_admission as module
    entered=Event();release=Event();events=[]
    def begin(*args):
        entered.set()
        if not release.wait(3):raise TimeoutError('Fixture release')
        events.append('committed')
        return 'active',1
    def finish(identifier):events.append('released')
    monkeypatch.setattr(module,'_identity',lambda:None)
    monkeypatch.setattr(module,'begin',begin)
    monkeypatch.setattr(module,'finish',finish)
    async def scenario():
        pending=asyncio.create_task(module.acquire('generation'))
        assert await asyncio.to_thread(entered.wait,2)
        pending.cancel();release.set()
        with pytest.raises(asyncio.CancelledError):await pending
    asyncio.run(scenario())
    assert events==['committed','released']
