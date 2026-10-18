import asyncio
from contextlib import suppress
import pytest
from fastapi import HTTPException
from nsai import encoder_service as encoder


def test_two_workers_and_query_queue_is_bounded_fifo_and_cancellation_safe(monkeypatch):
    async def run():
        monkeypatch.setattr(encoder,'_lock',asyncio.Lock())
        monkeypatch.setattr(encoder,'_admitted',0,raising=False)
        release=asyncio.Event();order=[]
        async def work(name):
            async with encoder._admission():
                order.append(name)
                if name=='first':await release.wait()
        first=asyncio.create_task(work('first'));await asyncio.sleep(0)
        second=asyncio.create_task(work('cancelled'));third=asyncio.create_task(work('third'))
        await asyncio.sleep(0)
        assert not second.done() and not third.done() and order==['first']
        with pytest.raises(HTTPException) as error:
            async with encoder._admission():pass
        assert error.value.status_code==429
        second.cancel()
        with suppress(asyncio.CancelledError):await second
        assert encoder._admitted==2 and encoder._lock.locked()
        fourth=asyncio.create_task(work('fourth'));await asyncio.sleep(0)
        release.set();await asyncio.gather(first,third,fourth)
        assert order==['first','third','fourth']
        assert encoder._admitted==0 and not encoder._lock.locked()
    asyncio.run(run())
