"""Source-bound claim comparison snapshots and exact event pagination; no authority token."""
from . import store
from .workflow_store import rows
from .contracts.evidence import canonical_hash
from .source_dependencies import collect_sources,validate_sources
from .citation_anchors import citation_from_hit
from .conversation_history import _number

FIELDS="c.id,c.document_id,c.subject,c.predicate,c.value,c.locator,c.status,c.revision,c.reviewed_by,c.source_ids,c.provenance_complete,d.title,d.source_version,d.media_type,d.ingested_by,d.original_sha256"


def _identity(claim_id):
    identity=store.request_identity()
    if identity is None:raise PermissionError('Claim inspection requires a verified identity')
    if not isinstance(claim_id,str) or not 1<=len(claim_id)<=128 or '\x00' in claim_id:
        raise ValueError('Invalid claim identity')
    return identity


def _target(conn,claim_id):
    _identity(claim_id)
    result=rows(conn.execute('SELECT '+FIELDS+",encode(sha256(d.source_bytes),'hex') AS observed_sha256 FROM claims c JOIN documents d ON d.id=c.document_id WHERE c.id=%s",(claim_id,)))
    if not result:raise LookupError('Claim unavailable')
    target=result[0]
    if target.pop('observed_sha256')!=target['original_sha256'] or target['original_sha256'] is None:
        raise ValueError('Original source integrity verification failed')
    return target


def review_context(conn,claim_id):
    identity=_identity(claim_id);target=_target(conn,claim_id)
    active=rows(conn.execute('SELECT '+FIELDS+" FROM claims c JOIN documents d ON d.id=c.document_id WHERE c.subject=%s AND c.predicate=%s AND c.id<>%s AND c.status NOT IN ('rejected','superseded') ORDER BY c.id LIMIT 2001",(target['subject'],target['predicate'],claim_id)))
    if len(active)>2000:raise ValueError('Review group exceeds the qualified 2000-alternative comparison bound; no partial acceptance is permitted')
    sources=collect_sources(target,active,conn=conn);validate_sources(conn,sources)
    context=canonical_hash(dict(schema='nsai.claim-review-context/1',actor=identity['actor'],role=identity['role'],claim=target,active_alternatives=active))
    return dict(claim=target,active_alternatives=active,context_sha256=context,source_dependencies=sources)


def detail(claim_id,*,offset=0):
    _identity(claim_id)
    if type(offset) is not int or not 0<=offset<=2000:raise ValueError('Invalid alternative page')
    with store.connect() as conn:
        result=review_context(conn,claim_id);target=result['claim'];alternatives=result.pop('active_alternatives')
        span=conn.execute('SELECT text FROM source_spans WHERE document_id=%s AND locator=%s',(target['document_id'],target['locator'])).fetchone()
        if span is None:raise LookupError('Original claim span unavailable')
        citation=citation_from_hit(dict(id=target['id'],document_id=target['document_id'],title=target['title'],revision=target['source_version'],original_sha256=target['original_sha256'],locator=target['locator'],text=span[0],extraction_complete=None,page_coverage=None))
        return dict(**result,citation=citation,alternatives=alternatives[offset:offset+25],total_alternatives=len(alternatives),offset=offset,limit=25,
            next_offset=offset+25 if offset+25<len(alternatives) else None,provenance_complete=True,
            can_review=store.request_identity()['role'] in {'reviewer','admin'} and store.request_identity()['actor']!=target['ingested_by'] and target['status'] not in {'rejected','superseded'},
            source_integrity='sha256-matches-original',context_schema='nsai.claim-review-context/1',
            limitation='Comparison covers the currently authorized subject/predicate group. Context hash grants no authority. Acceptance supersedes only alternatives locked by that transaction; newly concurrent candidates remain visible for fresh review.')


def events(claim_id,*,before_id=None):
    _identity(claim_id)
    position=_number(before_id) if before_id is not None else None
    with store.connect() as conn:
        target=_target(conn,claim_id);arguments=[claim_id]
        predicate=' AND id<%s' if position is not None else ''
        if position is not None:arguments.append(position)
        observed=rows(conn.execute('SELECT id::text AS id,event_type,actor,details,created_at FROM claim_events WHERE claim_id=%s'+predicate+' ORDER BY id DESC LIMIT 26',arguments))
        items=observed[:25];sources=collect_sources(target,items,conn=conn);validate_sources(conn,sources)
        return dict(claim_id=claim_id,items=items,has_more=len(observed)>25,next_before_id=items[-1]['id'] if len(observed)>25 else None,
            limit=25,source_dependencies=sources,provenance_complete=True,
            limitation='Currently authorized claim events; withheld rows are retained. This is not a global audit-chain or factual-correctness attestation.')
