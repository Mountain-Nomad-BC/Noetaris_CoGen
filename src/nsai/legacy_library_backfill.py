"""One-time legacy research projections; originals and historical locators stay immutable."""
import copy
import hashlib
import json
import os
import re
from . import store, research_store, semantic_jobs
from .contracts.source_envelope import SourceEnvelope


def prepare_legacy_projection(record, source_spans):
    if record.get('owner_scope')!='legacy-shared':
        raise PermissionError('Legacy maintenance cannot project private sources')
    document=record.get('id');revision=record.get('source_version')
    if not isinstance(document,str) or re.fullmatch('[a-f0-9]{32}',document) is None:
        raise ValueError('Legacy source identity is not supported')
    if not isinstance(revision,str) or not 1<=len(revision)<=50:
        raise ValueError('Legacy source revision is not supported')
    original=record.get('source_bytes');text=record.get('raw_text')
    if not isinstance(original,bytes) or not 1<=len(original)<=25*1024*1024:
        raise ValueError('Legacy original is missing or exceeds the preservation bound')
    digest=hashlib.sha256(original).hexdigest()
    if digest!=record.get('original_sha256'):
        raise ValueError('Legacy original custody mismatch')
    if not isinstance(text,str) or not text or len(text)>200000 or '\x00' in text:
        raise ValueError('Legacy text is outside the retained projection bound')
    manifest=record.get('manifest')
    if len(json.dumps(manifest,ensure_ascii=False,allow_nan=False).encode())>16*1024*1024:
        raise ValueError('Legacy manifest exceeds its preservation bound')
    envelope=SourceEnvelope.model_validate(manifest)
    if len(envelope.documents)!=1:
        raise ValueError('Legacy envelope requires one original source')
    source=envelope.documents[0];metadata=source.metadata
    if (source.source_id!=document or source.text!=text or metadata.get('revision')!=revision
            or metadata.get('original_sha256')!=digest or metadata.get('parser_version')!='nsai-bounded/1'):
        raise ValueError('Legacy envelope custody mismatch or unsupported parser history')
    spans=metadata.get('spans')
    if not isinstance(spans,list) or not 1<=len(spans)<=5000:
        raise ValueError('Legacy retained spans are outside the complete-processing bound')
    retained={};characters=0
    for span in spans:
        if not isinstance(span,dict):raise ValueError('Invalid retained legacy span')
        locator=span.get('locator');value=span.get('text')
        if (not isinstance(locator,str) or len(locator)>200
                or re.fullmatch(r'(?:line:[1-9]\d*|page:[1-9]\d*:line:[1-9]\d*)',locator) is None
                or not isinstance(value,str) or not value or '\x00' in value or locator in retained):
            raise ValueError('Invalid or duplicate retained legacy span')
        retained[locator]=value;characters+=len(value)
    if characters>200000 or len(source_spans)!=len(retained) or dict(source_spans)!=retained:
        raise ValueError('Legacy stored spans differ from the original retained envelope')
    parsed=dict(original_sha256=digest,raw_text=text,spans=copy.deepcopy(spans),complete=False,pages=[])
    artifacts=research_store.build(document,revision,parsed)
    knowledge=artifacts['knowledge']
    knowledge['extraction_coverage'].update(input_kind='legacy-retained-spans',
        legacy_parser_version='nsai-bounded/1',retained_manifest_sha256=research_store.artifact_hash(manifest))
    knowledge['graph_sha256']=research_store.artifact_hash({key:value for key,value in knowledge.items() if key!='graph_sha256'})
    return artifacts


def _maintenance_context():
    if store.request_identity() is not None:
        raise PermissionError('Legacy maintenance requires the internal service context')


def _commissioning_settings():
    if os.getenv('NSAI_INDEX_WORKER_ENABLED')!='true':
        raise RuntimeError('Commission the semantic worker before preparing legacy indexes')
    semantic_jobs.encoder_settings()


def commission_source(document):
    _maintenance_context()
    if not isinstance(document,str) or re.fullmatch('[a-f0-9]{32}',document) is None:
        raise ValueError('Invalid legacy source identity')
    _commissioning_settings()
    from .workflow_store import audit, rows
    with store.connect() as conn:
        # No document UPDATE authority is needed. A separate maintenance lock
        # serializes idempotent preparations; original source rows stay immutable.
        conn.execute('SELECT pg_advisory_xact_lock(878731)')
        size=conn.execute("SELECT octet_length(source_bytes),char_length(raw_text),octet_length(manifest::text) "
            "FROM documents WHERE id=%s AND owner_scope='legacy-shared'",(document,)).fetchone()
        if not size:raise LookupError('Legacy source unavailable')
        if (size[0] is None or not 1<=size[0]<=25*1024*1024 or not 1<=size[1]<=200000
                or size[2] is None or size[2]>16*1024*1024):
            raise ValueError('Legacy retained source exceeds preservation bounds')
        status=conn.execute('SELECT nsai_source_index_status(%s)',(document,)).fetchone()[0]
        if status['state']!='not-commissioned':
            return dict(document_id=document,queued=False,indexing=status)
        record=rows(conn.execute("SELECT id,source_version,original_sha256,source_bytes,raw_text,manifest,owner_scope,media_type "
            "FROM documents WHERE id=%s AND owner_scope='legacy-shared'",(document,)))[0]
        spans=conn.execute('SELECT locator,text FROM source_spans WHERE document_id=%s ORDER BY locator LIMIT 5001',(document,)).fetchall()
        artifacts=prepare_legacy_projection(record,spans)
        previous=conn.execute('SELECT artifact_sha256 FROM document_knowledge WHERE document_id=%s',(document,)).fetchone()
        if previous:
            # Historical research artifacts are immutable, too. Validate and
            # commission that exact existing generation instead of replacing it.
            saved=research_store.get(document,conn=conn,include_staged=True)
            if saved['revision']!=record['source_version']:raise ValueError('Legacy research revision mismatch')
            checksum=saved['artifact_sha256']
        else:
            checksum=research_store.artifact_hash(artifacts)
        audit(conn,'legacy-service','source.legacy-index-prepared',dict(document_id=document,
            original_sha256=record['original_sha256'],research_artifact_sha256=checksum,
            retained_manifest_sha256=research_store.artifact_hash(record['manifest']),extraction_coverage_verified=False))
        if not previous:
            research_store.persist(conn,document,record['source_version'],record['original_sha256'],artifacts)
        job=semantic_jobs.enqueue(conn,document,checksum)
        status=conn.execute('SELECT nsai_source_index_status(%s)',(document,)).fetchone()[0]
        if status['state']!='queued' or status.get('job_id')!=job:
            raise ValueError('Legacy index state requires reviewed reconciliation')
        return dict(document_id=document,queued=True,job_id=job,indexing=status)


def commission_batch(*,limit=100):
    _maintenance_context()
    if type(limit) is not int or not 1<=limit<=1000:
        raise ValueError('Legacy maintenance limit must be between 1 and 1000')
    _commissioning_settings()
    with store.connect() as conn:
        documents=[row[0] for row in conn.execute("SELECT id FROM documents WHERE owner_scope='legacy-shared' "
            "AND manifest#>>'{documents,0,metadata,parser_version}'='nsai-bounded/1' "
            "AND nsai_source_index_status(id)->>'state'='not-commissioned' ORDER BY id LIMIT %s",(limit+1,)).fetchall()]
    records=[commission_source(document) for document in documents[:limit]]
    return dict(records=records,has_more=len(documents)>limit,
        scope='Legacy parser-1 retained projections; extraction coverage remains unverified')


def main():
    import argparse
    import asyncio
    from .semantic_encoder import PINNED_MODEL_SHA256
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--limit',type=int,default=100)
    args=parser.parse_args()
    if not 1<=args.limit<=1000:parser.error('Limit must be between 1 and 1000')
    try:
        _commissioning_settings()
        identity=asyncio.run(semantic_jobs.encode_texts(['Legacy index generation identity check']))
        if identity.get('model_identity',{}).get('sha256')!=PINNED_MODEL_SHA256:
            raise ValueError('Legacy index encoder identity mismatch')
        result=commission_batch(limit=args.limit)
        print(json.dumps(dict(status='QUEUED',jobs_queued=sum(row['queued'] for row in result['records']),
            has_more=result['has_more'],publication_accepted=False)))
        return 1 if result['has_more'] else 0
    except Exception as error:
        print(json.dumps(dict(status='FAIL',error_type=type(error).__name__,originals_modified=False)))
        return 1


if __name__=='__main__':raise SystemExit(main())
