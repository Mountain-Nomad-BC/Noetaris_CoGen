from __future__ import annotations
import os
from pathlib import Path
from contextlib import contextmanager
from queue import LifoQueue, Empty
from threading import BoundedSemaphore, Lock
import hashlib
from contextvars import ContextVar
import re
from uuid import UUID

_request_identity=ContextVar('nsai_request_identity',default=None)
_request_sources=ContextVar('nsai_request_sources',default=None)


class AccessTrace:
    def __init__(self):self.sources=set();self.lock=Lock()
    def add(self,sources):
        with self.lock:
            self.sources.update(sources)
            if len(self.sources)>1000:raise ValueError('Request source budget exceeded')
    def snapshot(self):
        with self.lock:return sorted(self.sources)


def request_source_dependencies():
    trace=_request_sources.get()
    return trace.snapshot() if trace is not None else []


def request_identity():
    """Copy the server-verified request identity; never accept client scope data."""
    value=_request_identity.get()
    return dict(value) if value is not None else None


@contextmanager
def _bound_identity(identity):
    token=_request_identity.set(dict(identity))
    source_token=_request_sources.set(AccessTrace())
    try:yield
    finally:
        _request_sources.reset(source_token)
        _request_identity.reset(token)


@contextmanager
def identity_context(identity):
    actor=identity.get('actor');role=identity.get('role')
    if (not isinstance(actor,str) or not re.fullmatch(
            r'local-(?:user-[a-z][a-z0-9_-]{0,63}|operator|viewer|reviewer|admin)',actor)
            or role not in {'operator','viewer','reviewer','admin'}):
        raise ValueError('Invalid verified identity context')
    with _bound_identity(identity):yield


@contextmanager
def source_job_context(job):
    """Internal lease capability, restricted by database RLS to one source."""
    actor=job.get('actor');job_id=job.get('id');lease=job.get('lease_token')
    if (not isinstance(actor,str) or (actor!='legacy-service' and not re.fullmatch(r'local-user-[a-z][a-z0-9_-]{0,63}',actor))
        or not isinstance(job_id,str) or not re.fullmatch(r'[a-f0-9]{64}',job_id)
        or not isinstance(lease,str) or str(UUID(lease))!=lease):
        raise ValueError('Invalid source-job capability')
    identity=dict(actor=actor,role='operator' if actor!='legacy-service' else 'service',
                  identity_kind='source-job',permissions=[],job_id=job_id,job_lease=lease)
    with _bound_identity(identity):yield

_slots=BoundedSemaphore(4)
_idle=LifoQueue(maxsize=4)
_secret_cache={}
_secret_lock=Lock()


def _secret(path: str) -> str:
    source=Path(path)
    stat=source.stat()
    if not 32<=stat.st_size<=1026:
        raise RuntimeError('Configured secret exceeds bounded credential size')
    # NTFS timestamps can alias across a fast same-size atomic replacement.
    fingerprint=(str(source.resolve()),stat.st_dev,stat.st_ino,stat.st_mtime_ns,stat.st_size,stat.st_ctime_ns)
    with _secret_lock:
        cached=_secret_cache.get(path)
        if stat.st_ino and cached and cached[0]==fingerprint:return cached[1]
    value = source.read_text(encoding="utf-8").strip()
    if not value.isascii() or not 32<=len(value)<=1024 or any(ord(c)<=32 or ord(c)==127 for c in value):
        raise RuntimeError('Configured secret has invalid credential syntax')
    with _secret_lock:
        if len(_secret_cache)>16:_secret_cache.clear()
        _secret_cache[path]=(fingerprint,value)
    return value


def database_transport():
    """Explicit managed-PostgreSQL port and authenticated TLS; no DSN guessing."""
    import re
    import ipaddress
    host=os.environ.get('NSAI_DB_HOST','db')
    if not isinstance(host,str) or not host or len(host)>253:
        raise RuntimeError('Invalid database host')
    try:ipaddress.ip_address(host)
    except ValueError:
        if re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?',host) is None:
            raise RuntimeError('Invalid database host') from None
    port=os.getenv('NSAI_DB_PORT','5432')
    if re.fullmatch(r'[0-9]{1,5}',port) is None or not 1<=int(port)<=65535:
        raise RuntimeError('Invalid database port')
    local=host.lower() in {'db','localhost','127.0.0.1','::1'}
    mode=os.getenv('NSAI_DB_SSLMODE','prefer' if local else 'verify-full')
    if mode not in {'disable','allow','prefer','require','verify-ca','verify-full'}:
        raise RuntimeError('Invalid database TLS mode')
    if not local and mode!='verify-full':
        raise RuntimeError('Remote PostgreSQL requires verified TLS hostname and CA')
    result=dict(port=int(port),sslmode=mode)
    certificate=os.getenv('NSAI_DB_SSLROOTCERT_FILE','')
    if certificate:
        try:
            with Path(certificate).open('rb') as stream:raw=stream.read(131073)
        except OSError:raise RuntimeError('Database CA certificate unavailable') from None
        if not raw or len(raw)>131072 or b'-----BEGIN CERTIFICATE-----' not in raw:
            raise RuntimeError('Invalid or oversized database CA certificate')
        result['sslrootcert']=certificate
    elif not local:raise RuntimeError('Remote PostgreSQL requires a configured CA certificate file')
    return result


@contextmanager
def connect():
    from .resource_limits import capacity_profile
    resource_profile=capacity_profile()
    import psycopg  # imported lazily so pure-function checks do not need a running Postgres
    transport=database_transport()
    settings=dict(host=os.environ.get('NSAI_DB_HOST','db'),dbname=os.environ.get('NSAI_DB_NAME','nsai'),
        user=os.environ.get('NSAI_DB_USER','nsai_app'),password=_secret(os.environ['NSAI_DB_PASSWORD_FILE']),connect_timeout=3,
        options='-c statement_timeout=10000 -c lock_timeout=5000 -c idle_in_transaction_session_timeout=15000')
    settings.update(transport)
    trust_digest=None
    if 'sslrootcert' in transport:
        with Path(transport['sslrootcert']).open('rb') as stream:trust_bytes=stream.read(131073)
        if len(trust_bytes)>131072:raise RuntimeError('Database CA certificate grew beyond its bound')
        trust_digest=hashlib.sha256(trust_bytes).hexdigest()
    signature=hashlib.sha256(repr((sorted(settings.items()),trust_digest)).encode()).digest()
    if not _slots.acquire(timeout=3):raise RuntimeError('Database capacity busy')
    conn=None;verified=False;reusable=True
    try:
        while conn is None:
            try:previous,candidate=_idle.get_nowait()
            except Empty:break
            if previous==signature and not candidate.closed:conn=candidate
            else:candidate.close()
        if conn is None:conn=psycopg.connect(**settings)
        try:
            from .schema_contract import verify_database_contract
            verify_database_contract(conn)
            verified=True
            identity=request_identity()
            actor=identity['actor'] if identity else 'legacy-service'
            role=identity['role'] if identity else 'service'
            # Both values are set for every lease, including background/legacy
            # calls. LOCAL resets on commit/rollback; no pool authority survives.
            conn.execute("SELECT set_config('nsai.actor',%s,true),set_config('nsai.role',%s,true),"
                         "set_config('nsai.job_id',%s,true),set_config('nsai.job_lease',%s,true),"
                         "set_config('nsai.capacity_profile',%s,true)",
                         (actor,role,identity.get('job_id','') if identity else '',identity.get('job_lease','') if identity else '',resource_profile))
            yield conn
            trace=_request_sources.get()
            if trace is not None and identity.get('identity_kind') in {'local-user','source-job'}:
                dependencies=conn.execute('SELECT * FROM nsai_current_source_dependencies()').fetchall()
                trace.add(row[0] for row in dependencies)
            conn.commit()
        except BaseException:
            try:conn.rollback()
            except BaseException:
                reusable=False
                raise
            raise
    finally:
        if conn is not None:
            if not conn.closed:
                if verified and reusable:_idle.put_nowait((signature,conn))
                else:conn.close()
        _slots.release()


def store_document(title: str, text: str, version: str, actor: str = 'local-operator') -> dict:
    from .ingestion import parse_source
    from .workflow_store import persist_source
    return persist_source(title, version, text.encode('utf-8'), parse_source(text.encode('utf-8'), 'source.txt'), actor)


def all_claims() -> list[dict]:
    with connect() as conn:
        result=[row[0] for row in conn.execute('SELECT * FROM nsai_reflection_claims()')]
    if len(result)>2000:
        raise RuntimeError('Legacy corpus exceeds qualified claim capacity; conflict projection withheld')
    return result


def all_documents() -> list[dict]:
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id,title,source_version,coalesce(original_sha256,sha256),created_at,nsai_source_is_owner(id),nsai_source_index_status(id) FROM documents ORDER BY created_at DESC LIMIT 100")
            return [dict(zip(("id","title","version","sha256","created_at","can_manage_access","indexing"),row)) for row in cur.fetchall()]
