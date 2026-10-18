"""Short database transactions coordinate bounded operations across API workers."""
import asyncio
import time
import inspect
import os
from functools import wraps
from contextlib import asynccontextmanager,contextmanager
from uuid import uuid4
from . import store
from .operational_policy import operational_policy


class Busy(RuntimeError):
    pass


def enabled():
    value=os.getenv('NSAI_OPERATION_COORDINATION','false')
    if value not in {'true','false'}:raise ValueError('Invalid operation coordination setting')
    return value=='true'


def guarded(kind):
    def decorate(function):
        if inspect.iscoroutinefunction(function):
            @wraps(function)
            async def wrapped(*args,**kwargs):
                if not enabled():return await function(*args,**kwargs)
                try:
                    async with admitted(kind):return await function(*args,**kwargs)
                except Busy:
                    from fastapi import HTTPException
                    raise HTTPException(429,'Operation capacity reached; retry later',headers={'Retry-After':'1'}) from None
        else:
            @wraps(function)
            def wrapped(*args,**kwargs):
                if not enabled():return function(*args,**kwargs)
                try:
                    with admitted_sync(kind):return function(*args,**kwargs)
                except Busy:
                    from fastapi import HTTPException
                    raise HTTPException(429,'Operation capacity reached; retry later',headers={'Retry-After':'1'}) from None
        # Resolve forward annotations in the original API module, preserving
        # FastAPI validation and direct sync/async compatibility.
        wrapped.__signature__=inspect.signature(function,eval_str=True)
        return wrapped
    return decorate


def _identity():
    identity=store.request_identity()
    if not identity or identity.get('role')!='operator' or identity.get('identity_kind')=='source-job':
        raise PermissionError('Operation admission requires an operator')


def begin(identifier,kind):
    _identity();limits=operational_policy()
    if kind not in {'generation','ingestion'}:raise ValueError('Invalid operation kind')
    personal=limits.generations_per_user if kind=='generation' else limits.ingestions_per_user
    global_limit=limits.gpu_jobs if kind=='generation' else limits.concurrent_users
    queue=limits.gpu_queue if kind=='generation' else 0
    with store.connect() as conn:
        state=conn.execute('SELECT nsai_operation_begin(%s,%s,%s,%s,%s,%s)',
            (identifier,kind,limits.concurrent_users,personal,global_limit,queue)).fetchone()[0]
    if state not in {'active','queued'}:raise Busy('Operation admission: '+state)
    return state,global_limit


def finish(identifier):
    _identity()
    with store.connect() as conn:return conn.execute('SELECT nsai_operation_finish(%s)',(identifier,)).fetchone()[0]


def claim(identifier,global_limit):
    _identity()
    with store.connect() as conn:return conn.execute('SELECT nsai_operation_claim(%s,%s)',(identifier,global_limit)).fetchone()[0]


async def acquire(kind):
    _identity()
    identifier=uuid4().hex
    # All provider/parser deadlines are below this lease. Stream coordinators
    # must implement renewal before using this admission for long-lived streams.
    pending=asyncio.create_task(asyncio.to_thread(begin,identifier,kind))
    try:
        state,global_limit=await asyncio.shield(pending)
        deadline=time.monotonic()+30
        while state=='queued':
            if time.monotonic()>=deadline:raise Busy('Inference queue wait expired')
            await asyncio.sleep(.2)
            state=await asyncio.to_thread(claim,identifier,global_limit)
        if state!='active':raise Busy('Operation lease unavailable')
        return identifier
    except BaseException:
        # A cancelled await does not stop a database thread. Wait for its
        # transaction outcome before releasing, avoiding a late orphan commit.
        try:await asyncio.shield(pending)
        except Exception:pass
        await asyncio.shield(asyncio.to_thread(finish,identifier))
        raise


@asynccontextmanager
async def admitted(kind):
    identifier=await acquire(kind)
    try:yield
    finally:await asyncio.shield(asyncio.to_thread(finish,identifier))


@contextmanager
def admitted_sync(kind):
    identifier=uuid4().hex
    state,_=begin(identifier,kind)
    if state!='active':
        finish(identifier)
        raise Busy('Synchronous operation cannot wait in a queue')
    try:yield
    finally:finish(identifier)
