"""Private parser service: no database/model credentials, internal network only."""
import asyncio
import base64
import json
import os
import secrets
import sys
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from .upload_limits import ACTIVE
from .store import _secret
from .ingestion import MAX_PARSER_OUTPUT_BYTES, validate_parsed_source

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
lock = asyncio.Lock()

async def _bounded_read(stream, maximum):
    result = bytearray()
    while True:
        part = await stream.read(min(65536, maximum + 1 - len(result)))
        if not part:
            return bytes(result)
        result.extend(part)
        if len(result) > maximum:
            raise ValueError('Parser pipe budget exceeded')

async def _exchange(process, payload):
    async def write():
        process.stdin.write(payload)
        await process.stdin.drain()
        process.stdin.close()
    tasks = [asyncio.create_task(write()), asyncio.create_task(_bounded_read(process.stdout, MAX_PARSER_OUTPUT_BYTES)),
             asyncio.create_task(_bounded_read(process.stderr, 65536)), asyncio.create_task(process.wait())]
    try:
        results = await asyncio.gather(*tasks)
        return results[1]
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

class Source(BaseModel):
    model_config = ConfigDict(extra='forbid')
    filename: str = Field(min_length=1, max_length=180)
    data: str = Field(max_length=ACTIVE.base64_chars)

@app.get('/healthz')
def health(): return {'status': 'alive'}

@app.post('/parse')
async def parse(payload: Source, authorization: str | None = Header(default=None)):
    expected = _secret(os.environ['NSAI_PARSER_TOKEN_FILE'])
    if not isinstance(authorization,str) or len(authorization)>512 or not authorization.isascii() or not secrets.compare_digest(authorization, 'Bearer ' + expected):
        raise HTTPException(401, 'Unauthorized')
    if lock.locked():
        raise HTTPException(429, 'Parser busy')
    async with lock:
        process = await asyncio.create_subprocess_exec(sys.executable, '-m', 'nsai.parser_child',
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            env={'PATH': os.environ.get('PATH', ''), 'PYTHONPATH': os.environ.get('PYTHONPATH', ''), 'PYTHONDONTWRITEBYTECODE':'1', 'NSAI_UPLOAD_PROFILE':ACTIVE.profile})
        try:
            out = await asyncio.wait_for(_exchange(process, payload.model_dump_json().encode()), timeout=20)
            if process.returncode:
                raise HTTPException(422, 'Source cannot be parsed within safety limits')
            parsed = json.loads(out)
            validate_parsed_source(base64.b64decode(payload.data,validate=True), parsed)
            return parsed
        except (ValueError, UnicodeError, BrokenPipeError):
            raise HTTPException(422, 'Source cannot be parsed within safety limits') from None
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise HTTPException(422, 'Parser time limit exceeded') from None
        finally:
            if process.returncode is None:
                process.kill()
                await process.wait()
