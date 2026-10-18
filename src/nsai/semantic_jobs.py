"""Bounded durable orchestrator; the external encoder has no database credentials."""
import asyncio
import json
import logging
import os
import re
import httpx
from . import store,research_store
from .contracts.evidence import canonical_hash
from .semantic_encoder import PINNED_MODEL_SHA256

logger=logging.getLogger(__name__)


def worker_concurrency():
    value=os.getenv('NSAI_INDEX_CONCURRENCY','1')
    if value not in {'1','2'}:raise ValueError('Indexing concurrency must be 1 or 2')
    return int(value)


def active_actor_ids():
    """Validate the entire current server registry/credentials, without logging secrets."""
    from .security import _local_identities,resolve_principal,FILES
    entries=_local_identities()
    paths=[path for _,path in entries]+[os.environ[key] for key in FILES.values() if os.getenv(key)]
    if not paths:raise RuntimeError('Background indexing requires configured local authority')
    resolve_principal('Bearer '+store._secret(paths[0]))
    return sorted(entry['actor'] for entry,_ in entries)


def encoder_settings():
    url=os.getenv('NSAI_ENCODER_URL','')
    if url!='http://encoder:8092':raise ValueError('Encoder endpoint is not admitted')
    token=store._secret(os.environ['NSAI_ENCODER_TOKEN_FILE'])
    return url,token


def enqueue(conn,document_id,knowledge_sha256):
    job_id=canonical_hash(dict(schema_version='nsai.semantic-job/1',document_id=document_id,
        model_sha256=PINNED_MODEL_SHA256,knowledge_sha256=knowledge_sha256))
    return conn.execute('SELECT nsai_enqueue_semantic_job(%s,%s,%s,%s)',
        (job_id,document_id,PINNED_MODEL_SHA256,knowledge_sha256)).fetchone()[0]


def claim_next():
    if store.request_identity() is not None:raise PermissionError('Request identity cannot claim background jobs')
    actors=active_actor_ids()
    with store.connect() as conn:
        return conn.execute('SELECT nsai_claim_semantic_job(%s,%s,%s,300)',
            (PINNED_MODEL_SHA256,actors,worker_concurrency())).fetchone()[0]


def fail_job(job,code):
    if store.request_identity() is not None:raise PermissionError('Failure reconciliation requires orchestrator context')
    with store.connect() as conn:
        return conn.execute('SELECT nsai_fail_semantic_job(%s,%s,%s)',
                            (job['id'],job['lease_token'],code)).fetchone()[0]


def source_status(document_id):
    with store.connect() as conn:
        return conn.execute('SELECT nsai_source_index_status(%s)',(document_id,)).fetchone()[0]


def require_readable_index(document_id):
    with store.connect() as conn:
        if not conn.execute('SELECT nsai_index_source_readable(%s)',(document_id,)).fetchone()[0]:
            # Same response for unknown, inaccessible and unpublished sources.
            raise LookupError('Source index unavailable')


def _index_control(document_id,expected_epoch,operation,priority=None):
    identity=store.request_identity()
    if identity is None or identity.get('identity_kind')!='local-user' or identity.get('role')!='operator':
        raise LookupError('Source unavailable')
    statements={
        'retry':'SELECT nsai_retry_semantic_job(%s,%s)',
        'cancel':'SELECT nsai_cancel_semantic_job(%s,%s)',
        'priority':'SELECT nsai_set_semantic_job_priority(%s,%s,%s)',
    }
    if operation not in statements:raise ValueError('Unknown indexing control')
    from .source_dependencies import validate_sources
    from .workflow_store import audit
    with store.connect() as conn:
        if not conn.execute('SELECT nsai_source_is_owner(%s)',(document_id,)).fetchone()[0]:
            raise LookupError('Source unavailable')
        # Match publication/sharing lock order: source policy before job/ledger.
        validate_sources(conn,[document_id])
        parameters=(document_id,expected_epoch,priority) if operation=='priority' else (document_id,expected_epoch)
        changed=conn.execute(statements[operation],parameters).fetchone()[0]
        result=dict(job_id=changed,state='queued') if operation=='retry' else changed
        details=dict(document_id=document_id,job_id=result['job_id'],expected_epoch=expected_epoch,
                     epoch=expected_epoch+1,source_ids=[document_id])
        if operation=='priority':details['priority']=priority
        receipt=audit(conn,identity['actor'],'index.'+dict(retry='requeued',cancel='cancelled',priority='priority-changed')[operation],details)
    # Keep the established retry DTO; new controls return explicit audit proof.
    return result if operation=='retry' else dict(result,document_id=document_id,audit_receipt=receipt)


def retry(document_id,expected_epoch):
    return _index_control(document_id,expected_epoch,'retry')


def cancel(document_id,expected_epoch):
    return _index_control(document_id,expected_epoch,'cancel')


def set_priority(document_id,expected_epoch,priority):
    return _index_control(document_id,expected_epoch,'priority',priority)


async def encode_texts(texts):
    from .inference import _bounded_json
    endpoint,token=encoder_settings()
    async with httpx.AsyncClient(timeout=90,follow_redirects=False,trust_env=False) as client:
        return await _bounded_json(client,'POST',endpoint+'/encode',headers={'Authorization':'Bearer '+token},
            payload=dict(texts=texts),maximum=2*1024*1024,deadline=90)


def _load_checkpoints(job):
    with store.connect() as conn:
        return conn.execute('SELECT nsai_get_semantic_checkpoints(%s,%s)',
                            (job['id'],job['lease_token'])).fetchone()[0]


def _save_checkpoints(job,records):
    with store.connect() as conn:
        return conn.execute('SELECT nsai_put_semantic_checkpoints(%s,%s,%s::jsonb)',
            (job['id'],job['lease_token'],json.dumps(records,allow_nan=False))).fetchone()[0]


def _publish(job,vectors,coverage,model_identity):
    actors=active_actor_ids()
    with store.connect() as conn:
        stored=research_store.put_embeddings(job['document_id'],vectors,model_identity,coverage,
                                            job['actor'],conn=conn)
        publication=conn.execute('SELECT nsai_publish_semantic_job(%s,%s,%s,%s)',
            (job['id'],job['lease_token'],stored['artifact_sha256'],actors)).fetchone()[0]
    return dict(state='succeeded',publication_id=publication,embedding_sha256=stored['artifact_sha256'])


async def process_job(job,encode=encode_texts):
    from .knowledge import attach_embeddings
    with store.source_job_context(job):
        artifact=await asyncio.to_thread(research_store.get,job['document_id'])
        if artifact['artifact_sha256']!=job['knowledge_sha256'] or artifact['source_sha256']!=job['source_sha256']:
            raise ValueError('Job source generation mismatch')
        passages=[node for node in artifact['knowledge']['nodes'] if node['kind']=='passage']
        if not passages:raise ValueError('No supported passages to index')
        by_id={node['id']:node for node in passages}
        checkpoints=await asyncio.to_thread(_load_checkpoints,job)
        vectors={};coverage={};model_identity=None
        for node_id,record in checkpoints.items():
            if node_id not in by_id or record['artifact_sha256']!=research_store.artifact_hash(
                dict(node_id=node_id,vector=record['vector'],coverage=record['coverage'])):
                raise ValueError('Checkpoint source/content mismatch')
            vectors[node_id]=record['vector'];coverage[node_id]=record['coverage']
        remaining=[node for node in passages if node['id'] not in vectors]
        for offset in range(0,len(remaining),8):
            batch=remaining[offset:offset+8]
            encoded=await encode([node['text'] for node in batch])
            identity=encoded.get('model_identity',{})
            if identity.get('sha256')!=job['model_sha256']:
                raise ValueError('Encoder/job model identity mismatch')
            if model_identity is not None and model_identity!=identity:raise ValueError('Encoder identity changed during job')
            model_identity=identity
            if len(encoded.get('vectors',[]))!=len(batch) or len(encoded.get('coverage',[]))!=len(batch):
                raise ValueError('Encoder response inventory mismatch')
            selected_vectors={node['id']:vector for node,vector in zip(batch,encoded['vectors'])}
            selected_coverage={node['id']:item for node,item in zip(batch,encoded['coverage'])}
            validated=attach_embeddings(dict(nodes=batch),selected_vectors,identity,selected_coverage)
            records=[]
            for record in validated['embeddings']['records']:
                checkpoint=dict(node_id=record['node_id'],vector=record['vector'],coverage=record['coverage'])
                checkpoint['artifact_sha256']=research_store.artifact_hash(checkpoint)
                records.append(checkpoint)
                vectors[record['node_id']]=record['vector'];coverage[record['node_id']]=record['coverage']
            await asyncio.to_thread(_save_checkpoints,job,records)
        # A fully checkpointed retry still verifies the live encoder's identity.
        if model_identity is None:
            identity_check=await encode(['Index generation identity check'])
            model_identity=identity_check.get('model_identity',{})
            if model_identity.get('sha256')!=job['model_sha256']:raise ValueError('Resumed model identity mismatch')
        attach_embeddings(artifact['knowledge'],vectors,model_identity,coverage)
        return await asyncio.to_thread(_publish,job,vectors,coverage,model_identity)


def _lease_active(job):
    if store.request_identity() is not None:
        raise PermissionError('Lease reconciliation requires orchestrator context')
    with store.source_job_context(job):
        with store.connect() as conn:
            return conn.execute('SELECT nsai_job_source_allowed(%s)',(job['document_id'],)).fetchone()[0]


async def _process_with_lease(job):
    processing=asyncio.create_task(process_job(job))
    try:
        while True:
            completed,_=await asyncio.wait({processing},timeout=1)
            if completed:return await processing
            active=await asyncio.to_thread(_lease_active,job)
            # Publication may have committed while the authority probe ran.
            # A completed result remains authoritative; the SQL publication
            # boundary already validated the exact lease under its row lock.
            if processing.done():return await processing
            if not active:
                processing.cancel()
                try:await processing
                except asyncio.CancelledError:pass
                return dict(state='lease-released')
    finally:
        if not processing.done():
            processing.cancel()
            try:await processing
            except asyncio.CancelledError:pass


async def process_one():
    job=await asyncio.to_thread(claim_next)
    if job is None:return None
    try:
        async with asyncio.timeout(240):return await _process_with_lease(job)
    except asyncio.CancelledError:
        await asyncio.shield(asyncio.to_thread(fail_job,job,'cancelled'))
        raise
    except Exception as error:
        code=('capacity-exhausted' if getattr(error,'sqlstate',None)=='54000' else
              'stale-lease' if getattr(error,'sqlstate',None)=='40001' else
              'authorization-changed' if isinstance(error,(LookupError,PermissionError)) or getattr(error,'sqlstate',None)=='42501' else
              'encoder-unavailable' if isinstance(error,(httpx.HTTPError,TimeoutError)) else
              'invalid-artifact' if isinstance(error,ValueError) else 'processing-failed')
        reconciled=await asyncio.to_thread(fail_job,job,code)
        return dict(state='retry-scheduled' if reconciled else 'lease-released',error_code=code)


async def worker_loop():
    while True:
        try:
            result=await process_one()
            if result is None or result.get('state')!='succeeded':await asyncio.sleep(1)
        except asyncio.CancelledError:raise
        except Exception as error:
            logger.error('Background indexing iteration failed (%s)',type(error).__name__)
            await asyncio.sleep(5)
