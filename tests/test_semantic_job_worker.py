import asyncio

import pytest

from nsai import semantic_jobs


def test_worker_loop_logs_safe_error_type_and_continues(caplog,monkeypatch):
    attempts=0

    async def fail_once():
        nonlocal attempts
        attempts+=1
        if attempts==1:
            raise RuntimeError('private source payload')
        raise asyncio.CancelledError

    async def wait_before_retry(_delay):
        return None

    monkeypatch.setattr(semantic_jobs,'process_one',fail_once)
    monkeypatch.setattr(semantic_jobs.asyncio,'sleep',wait_before_retry)

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(semantic_jobs.worker_loop())

    assert attempts==2
    assert 'Background indexing iteration failed (RuntimeError)' in caplog.text
    assert 'private source payload' not in caplog.text
