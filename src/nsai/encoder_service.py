"""Bounded isolated CPU encoder: model mount and service token, no DB secrets."""
import asyncio
from contextlib import asynccontextmanager
import json
import os
import secrets
import sys
from typing import Annotated
from fastapi import FastAPI,HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel,ConfigDict,Field,model_validator
from .assembly import strict_json
from .store import _secret
from .semantic_encoder import PINNED_MODEL_SHA256

_lock=asyncio.Lock()
_admitted=0
_process=None
_stderr_task=None
_identity=None
_blocked=False


@asynccontextmanager
async def _admission():
    """One active child request plus two bounded FIFO waiters."""
    global _admitted
    if _admitted>=3:raise HTTPException(429,'Encoder queue full')
    _admitted+=1;acquired=False
    try:
        try:
            async with asyncio.timeout(15):await _lock.acquire()
            acquired=True
        except TimeoutError:raise HTTPException(503,'Encoder queue deadline exceeded') from None
        yield
    finally:
        if acquired:_lock.release()
        _admitted-=1


async def _stop():
    global _process,_stderr_task,_identity,_blocked
    process=_process
    if process is not None:
        if process.returncode is None:process.kill()
        try:await asyncio.wait_for(process.wait(),5)
        except TimeoutError:
            _blocked=True
            raise RuntimeError('Encoder process did not terminate') from None
    if _stderr_task is not None:
        _stderr_task.cancel();await asyncio.gather(_stderr_task,return_exceptions=True)
    _process=None;_stderr_task=None;_identity=None


async def _discard_errors(process):
    total=0
    while part:=await process.stderr.read(4096):
        total+=len(part)
        if total>65536:
            if process.returncode is None:process.kill()
            return


async def _frame(process,deadline):
    raw=await asyncio.wait_for(process.stdout.readline(),deadline)
    if not raw or len(raw)>2*1024*1024 or not raw.endswith(b'\n'):
        raise ValueError('Invalid bounded encoder response')
    return strict_json(raw,max_bytes=2*1024*1024,max_items=100000,max_depth=12)


async def _ready():
    global _process,_stderr_task,_identity
    if _blocked:raise RuntimeError('Encoder restart required')
    if _process is not None and _process.returncode is None:return _process
    await _stop()
    environment={key:os.environ[key] for key in ['PATH','PYTHONPATH'] if key in os.environ}
    environment.update(NSAI_ENCODER_MODEL_DIR=os.environ['NSAI_ENCODER_MODEL_DIR'],
        PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
        TOKENIZERS_PARALLELISM='false',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='1')
    _process=await asyncio.create_subprocess_exec(sys.executable,'-m','nsai.semantic_child',
        stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE,
        limit=2*1024*1024+1,env=environment)
    _stderr_task=asyncio.create_task(_discard_errors(_process))
    greeting=await _frame(_process,30)
    if greeting.get('status')!='ready' or greeting.get('model_identity',{}).get('sha256')!=PINNED_MODEL_SHA256:
        raise ValueError('Encoder model identity mismatch')
    _identity=greeting['model_identity']
    return _process


@asynccontextmanager
async def lifespan(app):
    global _lock,_admitted
    _lock=asyncio.Lock();_admitted=0
    try:yield
    finally:await _stop()


app=FastAPI(docs_url=None,redoc_url=None,openapi_url=None,lifespan=lifespan)


@app.middleware('http')
async def bounds(request,call_next):
    if request.url.path not in {'/healthz','/identity','/encode'}:
        return JSONResponse({'detail':'Not found'},404)
    if request.url.path!='/healthz':
        try:expected=_secret(os.environ['NSAI_ENCODER_TOKEN_FILE'])
        except Exception:return JSONResponse({'detail':'Encoder authentication unavailable'},503)
        supplied=request.headers.get('Authorization')
        if (not isinstance(supplied,str) or len(supplied)>1031 or not supplied.isascii()
            or not secrets.compare_digest(supplied,'Bearer '+expected)):
            return JSONResponse({'detail':'Unauthorized'},401)
    if request.method=='POST':
        total=0;parts=[]
        try:
            async with asyncio.timeout(10):
                async for part in request.stream():
                    total+=len(part)
                    if total>1200*1024:return JSONResponse({'detail':'Encoder request exceeded'},413)
                    parts.append(part)
            request._body=b''.join(parts)
            strict_json(request._body,max_bytes=1200*1024,max_items=10000,max_depth=4)
        except TimeoutError:return JSONResponse({'detail':'Encoder request deadline exceeded'},408)
        except ValueError:return JSONResponse({'detail':'Invalid encoder JSON'},422)
    response=await call_next(request)
    response.headers.update({'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'})
    return response


class EncoderBatch(BaseModel):
    model_config=ConfigDict(extra='forbid')
    texts:list[Annotated[str,Field(min_length=1,max_length=131072)]]=Field(min_length=1,max_length=8)
    @model_validator(mode='after')
    def byte_limits(self):
        sizes=[len(text.encode()) for text in self.texts]
        if any(not text.strip() for text in self.texts) or max(sizes)>128*1024 or sum(sizes)>1024*1024:
            raise ValueError('Encoder passage byte budget exceeded')
        return self


@app.get('/healthz')
def health():
    if _blocked:raise HTTPException(503,'Encoder restart required')
    return dict(status='alive',model_loaded=_process is not None and _process.returncode is None)


@app.get('/identity')
async def identity():
    async with _admission():
        try:
            await _ready()
            return dict(model_identity=_identity)
        except Exception:
            await _stop()
            raise HTTPException(503,'Encoder unavailable') from None


@app.post('/encode')
async def encode(payload:EncoderBatch):
    async with _admission():
        try:
            process=await _ready()
            raw=json.dumps(dict(texts=payload.texts),ensure_ascii=False,allow_nan=False).encode()+b'\n'
            process.stdin.write(raw)
            await asyncio.wait_for(process.stdin.drain(),10)
            result=await _frame(process,60)
            if result.get('status')!='ok':raise ValueError('Encoder rejected source')
            encoded=result['result']
            if encoded.get('model_identity')!=_identity or len(encoded.get('vectors',[]))!=len(payload.texts):
                raise ValueError('Encoder response identity/inventory mismatch')
            return encoded
        except asyncio.CancelledError:
            await asyncio.shield(_stop())
            raise
        except Exception:
            await _stop()
            raise HTTPException(422,'Encoder rejected source or exceeded limits') from None
