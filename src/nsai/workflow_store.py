"""Transactional workflow owner; immutable sources, scoped sessions, independent review."""
from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from uuid import uuid4
from . import store
from .contracts.evidence import canonical_hash, CandidateClaim, EvidenceSource
from .models import extract_claims
from .contracts.source_envelope import SourceEnvelope, SourceDocument
from .contracts.memory_plan import build_memory_query_plan

PROJECT = 'amd-hackathon-local'

def rows(cursor):
    keys = [column.name for column in cursor.description]
    return [dict(zip(keys, row)) for row in cursor.fetchall()]

def audit(conn, actor, event, details):
    from .source_dependencies import collect_sources,validate_sources
    sources=collect_sources(details,conn=conn)
    # Policy locks must precede the global ledger lock, matching sharing and
    # content transactions. INSERT RLS rechecks these same held dependencies.
    validate_sources(conn,sources)
    conn.execute('SELECT pg_advisory_xact_lock(878701)')
    previous = conn.execute('SELECT nsai_audit_head()').fetchone()[0]
    body = dict(actor=actor, event_type=event, details=details, previous_sha256=previous)
    digest = canonical_hash(body)
    conn.execute('INSERT INTO audit_events(actor,event_type,details,previous_sha256,sha256,source_ids,provenance_complete) VALUES(%s,%s,%s::jsonb,%s,%s,%s,true)',
        (actor,event,json.dumps(details),previous,digest,sources))
    return digest

def persist_source(title, version, original, parsed, actor):
    from .ingestion import validate_parsed_source
    validate_parsed_source(original,parsed)
    digest = hashlib.sha256(original).hexdigest()
    if digest != parsed['original_sha256']:
        raise ValueError('Parser provenance mismatch')
    identity=store.request_identity()
    private=actor.startswith('local-user-')
    if private and (identity is None or identity['actor']!=actor or identity['role']!='operator'):
        raise PermissionError('Private ingestion requires a verified owner context')
    owner_scope=actor if private else 'legacy-shared'
    # Preserve all legacy IDs; new private logical sources deduplicate only
    # within the immutable uploader boundary, even for identical bytes.
    identity_bytes=(json.dumps([actor,version,digest],separators=(',',':')) if private
                    else f'{version}:{digest}')
    doc_id = hashlib.sha256(identity_bytes.encode()).hexdigest()[:32]
    from . import research_store
    research_artifacts = research_store.build(doc_id, version, parsed)
    from .models import observe_statements
    manifest = SourceEnvelope(index_name=PROJECT, documents=[SourceDocument(source_id=doc_id,
        title=title, text=parsed['raw_text'], metadata=dict(revision=version, original_sha256=digest,
            parser_version=parsed['parser_version'], spans=parsed['spans'], warnings=parsed['warnings'],
            pages=parsed.get('pages',[]),complete=parsed.get('complete',True),chunks=parsed['chunks'],
            normalization_map=parsed.get('normalization_map',[]),ocr_words=parsed.get('ocr_words',[]),
            extraction_history=parsed.get('extraction_history',[]),
            observations=observe_statements(parsed['raw_text']),
            **({'structured_data':parsed['structured_data']} if 'structured_data' in parsed else {})))])
    created_claims = []
    with store.connect() as conn:
        conn.execute('SELECT pg_advisory_xact_lock(878704)')
        exists=conn.execute('SELECT 1 FROM documents WHERE id=%s',(doc_id,)).fetchone()
        if not exists:
            proposed=sum(len(extract_claims(s['text'])) for s in parsed['spans'])
            if not conn.execute('SELECT nsai_source_capacity_available(%s)',(proposed,)).fetchone()[0]:
                raise ValueError('Source or claim capacity reached; contact the local administrator')
        inserted = conn.execute('INSERT INTO documents(id,title,source_version,sha256,raw_text,source_bytes,original_sha256,media_type,manifest,ingested_by,owner_scope) '
            'VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s) ON CONFLICT(owner_scope,sha256,source_version) DO NOTHING',
            (doc_id,title,version,digest,parsed['raw_text'],original,digest,parsed['media_type'],manifest.model_dump_json(),actor,owner_scope)).rowcount > 0
        if inserted:
            for span in parsed['spans']:
                conn.execute('INSERT INTO source_spans(document_id,locator,text) VALUES(%s,%s,%s)', (doc_id,span['locator'],span['text']))
                for claim in extract_claims(span['text']):
                    claim_id = canonical_hash(dict(document_id=doc_id, locator=span['locator'], subject=claim.subject,
                        predicate=claim.predicate,value=claim.value))[:32]
                    CandidateClaim(claim_id=claim_id,subject=claim.subject,predicate=claim.predicate,value=claim.value,
                        source=EvidenceSource(document_id=doc_id,revision=version,content_sha256=digest,
                            locator=span['locator'],media_type=parsed['media_type']),observed_at=datetime.now(timezone.utc))
                    conn.execute('INSERT INTO claims(id,document_id,subject,predicate,value,locator) VALUES(%s,%s,%s,%s,%s,%s)',
                        (claim_id,doc_id,claim.subject,claim.predicate,claim.value,span['locator']))
                    conn.execute('INSERT INTO claim_events(claim_id,event_type,actor) VALUES(%s,%s,%s)', (claim_id,'claim.candidate.created',actor))
                    created_claims.append(claim_id)
            for chunk in parsed['chunks']:
                chunk_id = canonical_hash(dict(document_id=doc_id,locator=chunk['locator'],offset=chunk['offset'],sha256=chunk['sha256']))[:32]
                conn.execute('INSERT INTO chunks(id,document_id,locator,text,sha256) VALUES(%s,%s,%s,%s,%s)',
                    (chunk_id,doc_id,chunk['locator'],chunk['text'],chunk['sha256']))
            receipt = audit(conn,actor,'source.ingested', dict(document_id=doc_id,original_sha256=digest,
                chunks=len(parsed['chunks']),candidate_claims=len(created_claims),manifest_sha256=canonical_hash(manifest.model_dump(mode='json')),
                research_artifact_sha256=research_store.artifact_hash(research_artifacts)))
        research_sha256 = research_store.persist(conn, doc_id, version, digest, research_artifacts)
        from .semantic_jobs import enqueue
        index_job=enqueue(conn,doc_id,research_sha256)
        indexing=conn.execute('SELECT nsai_source_index_status(%s)',(doc_id,)).fetchone()[0]
        if not inserted:
            receipt = None
    return dict(document_id=doc_id,sha256=digest,created=inserted,candidate_claims=len(created_claims),
        chunks=len(parsed['chunks']),warnings=parsed['warnings'],audit_receipt=receipt,
        research_artifact_sha256=research_sha256,semantic_embeddings=indexing['state'],index_job=index_job,indexing=indexing,
        knowledge_state='source-observation-candidates',formulas=len(research_artifacts['formulas']['records']))

def source(document_id, locator=None):
    with store.connect() as conn:
        doc = rows(conn.execute('SELECT id,title,source_version AS revision,original_sha256,media_type,raw_text,manifest,nsai_source_is_owner(id) AS can_manage_access,nsai_source_index_status(id) AS indexing FROM documents WHERE id=%s', (document_id,)))
        if not doc: raise LookupError('Source not found')
        result = doc[0]
        if locator:
            span = conn.execute('SELECT text FROM source_spans WHERE document_id=%s AND locator=%s', (document_id,locator)).fetchone()
            if not span: raise LookupError('Source span not found')
            result.update(locator=locator,text=span[0])
        return result

def original_source(document_id):
    with store.connect() as conn:
        row = conn.execute('SELECT source_bytes,original_sha256,media_type FROM documents WHERE id=%s', (document_id,)).fetchone()
        if not row or row[0] is None: raise LookupError('Original source unavailable')
        data = bytes(row[0])
        if hashlib.sha256(data).hexdigest() != row[1]: raise ValueError('Source integrity failure')
        return data,row[2]

class RetrievalHits(list):
    """List-compatible lexical matches with a bounded limit-omission receipt."""
    def __init__(self, observed, limit):
        additional=len(observed)>limit
        super().__init__(observed[:limit])
        self.coverage=dict(method='lexical',returned_chunks=len(self),limit=limit,
            additional_matches_exist=additional,matching_chunks_lower_bound=len(observed),
            omitted_chunks_at_least=max(0,len(observed)-limit),
            total_matching_chunks=None if additional else len(observed))


def retrieve(question, limit=12, *, document_ids=None, revision=None, pages=None):
    if not 1<=limit<=50:raise ValueError('Invalid retrieval limit')
    from .retrieval.query import build_retrieval_query
    query=build_retrieval_query(question)
    with store.connect() as conn:
        observed=[row[0] for row in conn.execute(
            'SELECT * FROM nsai_library_lexical_search(%s,%s,%s,%s,%s,%s,%s)',
            (query.exact,query.alternate,query.entity_gate,document_ids or None,revision,pages or None,limit+1)).fetchall()]
    return RetrievalHits(observed,limit)

def review(claim_id, decision, expected_revision, rationale, actor, expected_context=None):
    with store.connect() as conn:
        # Serialize group decisions before taking row locks to avoid competing promotion deadlocks.
        conn.execute('SELECT pg_advisory_xact_lock(878702)')
        match = rows(conn.execute('SELECT c.*,d.ingested_by,d.source_bytes,d.original_sha256 FROM claims c JOIN documents d ON d.id=c.document_id WHERE c.id=%s FOR UPDATE OF c', (claim_id,)))
        if not match: raise LookupError('Claim not found')
        claim = match[0]
        if claim['revision'] != expected_revision: raise ValueError('Stale claim revision; refresh before review')
        if actor == claim['ingested_by']: raise PermissionError('Reviewer must be independent of source submitter')
        if claim['status'] in {'rejected','superseded'}: raise ValueError('Closed claim cannot be reviewed')
        if hashlib.sha256(bytes(claim['source_bytes'])).hexdigest() != claim['original_sha256']:
            raise ValueError('Source integrity verification failed')
        state = dict(accept='verified',reject='rejected',contest='contested')[decision]
        alternatives=[]
        if decision == 'accept':
            alternatives=rows(conn.execute("SELECT id,status,revision,document_id FROM claims WHERE subject=%s AND predicate=%s AND id<>%s AND status NOT IN ('rejected','superseded') FOR UPDATE",
                (claim['subject'],claim['predicate'],claim_id)))
        comparison_sources=[]
        if expected_context is not None:
            from .claim_review import review_context
            comparison=review_context(conn,claim_id)
            observed_context=comparison['context_sha256']
            if observed_context!=expected_context:raise ValueError('Review comparison context changed; reload all alternatives')
            comparison_sources=comparison['source_dependencies']
        from .source_dependencies import collect_sources
        sources=collect_sources(claim,alternatives,dict(source_ids=comparison_sources),required=[claim['document_id']],conn=conn)
        if decision == 'accept':
            # Preserve all alternatives; projection changes are distinct from source destruction.
            conn.execute("UPDATE claims SET status='superseded',revision=revision+1,reviewed_by=%s,source_ids=%s,provenance_complete=true WHERE id=ANY(%s)",
                (actor,sources,[alternative['id'] for alternative in alternatives]))
        conn.execute('UPDATE claims SET status=%s,revision=revision+1,reviewed_by=%s,source_ids=%s,provenance_complete=true WHERE id=%s', (state,actor,sources,claim_id))
        details=dict(claim_id=claim_id,old_state=claim['status'],new_state=state,old_revision=expected_revision,
            new_revision=expected_revision+1,rationale=rationale,document_id=claim['document_id'],source_ids=sources,
            source_sha256=claim['original_sha256'],alternatives_superseded=alternatives,review_context_sha256=expected_context)
        for alternative in alternatives:
            conn.execute('INSERT INTO claim_events(claim_id,event_type,actor,details) VALUES(%s,%s,%s,%s::jsonb)',
                (alternative['id'],'claim.superseded',actor,json.dumps(dict(chosen_claim_id=claim_id,
                    old_state=alternative['status'],old_revision=alternative['revision'],new_revision=alternative['revision']+1))))
        conn.execute('INSERT INTO claim_events(claim_id,event_type,actor,details) VALUES(%s,%s,%s,%s::jsonb)',
            (claim_id,'claim.reviewed',actor,json.dumps(details)))
        return dict(claim_id=claim_id,state=state,revision=expected_revision+1,context_sha256=expected_context,
            superseded_count=len(alternatives),audit_receipt=audit(conn,actor,'claim.reviewed',details))

def session(actor, session_id=None):
    with store.connect() as conn:
        if session_id:
            row = conn.execute('SELECT owner FROM sessions WHERE id=%s', (session_id,)).fetchone()
            if not row or row[0] != actor: raise PermissionError('Session unavailable to this identity')
        else:
            session_id = uuid4().hex
            conn.execute('INSERT INTO sessions(id,owner) VALUES(%s,%s)', (session_id,actor))
        return session_id

def save_exchange(session_id, question, result, actor):
    from .source_dependencies import stored_provenance
    sources,complete=stored_provenance(result)
    if actor.startswith('local-user-') and not complete:
        raise ValueError('Private exchange requires complete source provenance')
    with store.connect() as conn:
        for role,text,receipt in [('user',question,{}),('assistant',result['answer'],result)]:
            conn.execute('INSERT INTO session_messages(session_id,role,text,receipt,source_ids,provenance_complete) VALUES(%s,%s,%s,%s::jsonb,%s,%s)', (session_id,role,text[:12000],json.dumps(receipt),sources,complete))
        audit(conn,actor,'chat.completed',dict(session_id=session_id,mode=result['mode'],citation_count=len(result['citations']),source_ids=sources))

def _claim_scope(document_ids=None, revision=None, pages=None):
    if pages is not None and (not isinstance(pages,list) or any(type(p) is not int or not 1<=p<=1000 for p in pages)):
        raise ValueError('Memory pages must be page numbers between 1 and 1000')
    conditions=[];arguments=[]
    if document_ids:
        conditions.append('c.document_id=ANY(%s)');arguments.append(document_ids)
    if revision is not None:
        conditions.append('d.source_version=%s');arguments.append(revision)
    if pages:
        conditions.append("c.locator LIKE 'page:%%' AND split_part(c.locator,':',2)=ANY(%s)");arguments.append([str(p) for p in pages])
    conditions.append('nsai_index_source_readable(c.document_id)')
    return ' AND '.join(conditions),arguments


def scoped_claims(*,document_ids=None,revision=None,pages=None,active_only=False):
    """Bound claim projection after exact source/revision/page restrictions."""
    if type(active_only) is not bool:raise ValueError('Active-only flag must be boolean')
    scope_sql,arguments=_claim_scope(document_ids,revision,pages)
    if active_only:scope_sql+=" AND c.status NOT IN ('superseded','rejected')"
    with store.connect() as conn:
        claims=rows(conn.execute("SELECT c.id,c.subject,c.predicate,c.value,c.locator,c.document_id,c.revision,c.reviewed_by,c.status,c.source_ids,c.provenance_complete,d.original_sha256 FROM claims c JOIN documents d ON d.id=c.document_id WHERE "+scope_sql+" ORDER BY c.id LIMIT 2001",arguments))
    if len(claims)>2000:raise RuntimeError('Scoped corpus exceeds qualified claim capacity; projection withheld')
    return claims


def claim_context(hits,*,document_ids=None,revision=None,pages=None):
    """Return hit claims and one witness per raw alternative in their groups.

    Distinct raw values stay distinct until exact Python quantity comparison.
    Result bounds fail closed; no conflicting alternative is silently truncated.
    """
    spans=sorted({(hit['document_id'],locator) for hit in hits for locator in
                  [hit['locator'],*[segment['locator'] for segment in hit.get('source_segments',[])]]})
    if not spans:return []
    if len(spans)>2000:raise ValueError('Passage source context exceeds bounds')
    _claim_scope(document_ids,revision,pages)
    with store.connect() as conn:
        result=[row[0] for row in conn.execute(
            'SELECT * FROM nsai_claim_context(%s::jsonb,%s::text[],%s,%s::integer[])',
            [json.dumps([dict(document_id=doc,locator=loc) for doc,loc in spans]),
             document_ids or None,revision,pages or None])]
    if len(result)>2000:raise RuntimeError('Relevant claim alternatives exceed qualified capacity; synthesis withheld')
    return result


def memory_claims(question='',*,document_ids=None,revision=None,pages=None):
    """Bound candidate selection, then check all alternatives of selected groups."""
    _claim_scope(document_ids,revision,pages)
    with store.connect() as conn:
        seeds=[row[0] for row in conn.execute(
            'SELECT * FROM nsai_memory_claim_seeds(%s,%s::text[],%s,%s::integer[])',
            [question[:1000],document_ids or None,revision,pages or None])]
    return claim_context(seeds,document_ids=document_ids,revision=revision,pages=pages)


def memory_context(actor, session_id, question='', *, document_ids=None, revision=None, pages=None):
    session(actor, session_id)
    import re
    scope_sql,arguments=_claim_scope(document_ids,revision,pages)
    claims=memory_claims(question,document_ids=document_ids,revision=revision,pages=pages)
    explicit_scope=bool(document_ids) or revision is not None or bool(pages)
    with store.connect() as conn:
        working=[] if explicit_scope else rows(conn.execute("SELECT role,text,created_at,source_ids,provenance_complete,receipt FROM session_messages WHERE session_id=%s AND created_at>now()-interval '1 day' ORDER BY id DESC LIMIT 8",(session_id,)))
        canon=[claim for claim in claims if claim['status']=='verified']
        reflection=rows(conn.execute("SELECT l.id,l.source_claim_id,l.reflection,l.state,l.source_ids,l.provenance_complete FROM learning_proposals l JOIN claims c ON c.id=l.source_claim_id JOIN documents d ON d.id=c.document_id WHERE l.author=%s AND l.state<>'rejected' AND c.status NOT IN ('superseded','rejected') AND "+scope_sql+" ORDER BY l.created_at DESC,l.id LIMIT 8",[actor,*arguments]))
    from .answer_support import response_is_current
    omitted=sum(message['role']=='assistant' and not response_is_current(message.get('receipt')) for message in working)
    working=[message for message in reversed(working) if message['role']!='assistant' or response_is_current(message.get('receipt'))]
    for message in working:message.pop('receipt',None)
    words=set(re.findall(r'\w+',question.lower()))
    canon.sort(key=lambda c:(-len(words & set(re.findall(r'\w+',(' '.join([c['subject'],c['predicate'],c['value']])).lower()))),c['id']))
    for message in working:
        message['created_at']=message['created_at'].isoformat()
    from .models import conflict_groups
    hypotheses = conflict_groups(claims)
    from .memory import materialize_projection
    projection=materialize_projection(working,canon,reflection,hypotheses,max_bytes=12000)
    bindings = [c['id'] for c in projection['canon']] or ['empty-canon']
    source_scope=dict(document_ids=sorted(document_ids or []),revision=revision,pages=sorted(set(pages or [])))
    research=None
    if document_ids:
        from .research_store import memory_candidates
        research=memory_candidates(document_ids,question,revision,pages)
    source_revision = canonical_hash(dict(canon=canon,hypotheses=hypotheses,source_scope=source_scope,research_candidates=research))
    plan = build_memory_query_plan(project_id=PROJECT,subject_id=session_id,actor_id=actor,agent_id='nsai-assistant',
        binding_ids=bindings,memory_classes=['knowledge'],tiers=['canon'],max_items=12,max_bytes=16384,max_tokens=4096,
        trust_floor=1.0,max_age_seconds=86400,conflict_policy='quarantine',provenance_required=True,
        writeback_policy='proposal_only',source_revision=source_revision,dependency_revisions={'nsai':'1'})
    envelope=dict(project_id=PROJECT,**projection,plan=plan.as_dict(),source_scope=source_scope,
                  working_support_policy_omissions=omitted,
                  claim_selection=dict(method='bounded-lexical-memory-seeds-and-alternative-witnesses',
                                       seed_limit=12,hypotheses_scope='selected-claim-groups',exhaustive_corpus=False))
    if research is not None:
        envelope['research_candidates']=research
    from .source_dependencies import collect_sources
    dependencies=collect_sources(envelope,required=store.request_source_dependencies())
    if len(json.dumps(dependencies).encode())>2048:
        from .provenance_manifests import register
        envelope['source_manifest_id']=register(dependencies)
        envelope['source_dependency_count']=len(dependencies)
    else:envelope['source_dependencies']=dependencies
    envelope['provenance_complete']=True
    envelope['envelope_max_bytes']=16384
    envelope['envelope_bytes']=0
    for _ in range(3):envelope['envelope_bytes']=len(json.dumps(envelope,ensure_ascii=False,allow_nan=False).encode())
    if envelope['envelope_bytes']>16384:raise ValueError('Complete memory envelope exceeds budget')
    return envelope

def propose_learning(actor, source_claim_id, reflection, *, source_ids=None):
    with store.connect() as conn:
        conn.execute('SELECT pg_advisory_xact_lock(878703)')
        claim = conn.execute('SELECT document_id,source_ids FROM claims WHERE id=%s', (source_claim_id,)).fetchone()
        if not claim: raise LookupError('Learning requires an attributable source claim')
        from .source_dependencies import collect_sources
        sources=collect_sources(dict(source_ids=source_ids or []),dict(source_ids=claim[1]),required=[claim[0]],conn=conn)
        identity=dict(author=actor,source_claim_id=source_claim_id,reflection=reflection)
        if actor.startswith('local-user-'):identity['source_ids']=sources
        pid=canonical_hash(identity)[:32]
        previous=conn.execute('SELECT state FROM learning_proposals WHERE id=%s',(pid,)).fetchone()
        if previous:return dict(id=pid,state=previous[0],created=False,authority_granted=False)
        count = conn.execute("SELECT count(*) FROM learning_proposals WHERE author=%s AND state='candidate'", (actor,)).fetchone()[0]
        if count >= 20: raise ValueError('At most 20 pending learning proposals per identity')
        conn.execute('INSERT INTO learning_proposals(id,author,source_claim_id,reflection,source_ids,provenance_complete) VALUES(%s,%s,%s,%s,%s,true)', (pid,actor,source_claim_id,reflection,sources))
        return dict(id=pid,state='candidate',created=True,authority_granted=False,audit_receipt=audit(conn,actor,'learning.proposed',dict(id=pid,source_claim_id=source_claim_id,source_ids=sources)))

def reflect_on_conflicts(actor):
    from .models import conflict_groups
    claims = [r for r in store.all_claims() if r['status'] not in {'superseded','rejected'}]
    groups = conflict_groups(claims)[:4]
    created = 0
    for group in groups:
        first = next(iter(group['alternatives'].values()))[0]['claim_id']
        reflection = f"Observed conflicting source revisions for {group['subject']} / {group['predicate']}: {', '.join(group['alternatives'])}. Compare original spans and request independent review; no value is automatically canonical."
        with store.connect() as conn:
            prior = conn.execute('SELECT 1 FROM learning_proposals WHERE author=%s AND source_claim_id=%s AND reflection=%s', (actor,first,reflection)).fetchone()
        if not prior:
            from .source_dependencies import collect_sources
            proposal=propose_learning(actor,first,reflection[:2000],source_ids=collect_sources(group)); created += int(proposal.get('created',False))
    return dict(created=created,authority_granted=False,method='deterministic conflict reflection; no model weight training')

def proposals():
    with store.connect() as conn:
        return rows(conn.execute('SELECT * FROM learning_proposals ORDER BY created_at DESC LIMIT 100'))

def review_learning(actor, pid, expected_revision, approve, rationale=None):
    if type(expected_revision) is not int or expected_revision<1 or type(approve) is not bool:
        raise ValueError('Invalid proposal review transition')
    if rationale is not None and (not isinstance(rationale,str) or not 10<=len(rationale)<=2000 or not rationale.strip()):
        raise ValueError('Review rationale requires 10 to 2000 characters')
    with store.connect() as conn:
        record = rows(conn.execute('SELECT * FROM learning_proposals WHERE id=%s FOR UPDATE', (pid,)))
        if not record: raise LookupError('Proposal not found')
        row = record[0]
        if row['author'] == actor: raise PermissionError('Independent reviewer required')
        if row['revision'] != expected_revision or row['state'] != 'candidate': raise ValueError('Stale or closed proposal')
        state = 'reviewed' if approve else 'rejected'
        conn.execute('UPDATE learning_proposals SET state=%s,revision=revision+1 WHERE id=%s', (state,pid))
        return dict(id=pid,state=state,revision=expected_revision+1,authority_granted=False,
            audit_receipt=audit(conn,actor,'learning.reviewed',dict(id=pid,state=state,
                previous_state=row['state'],previous_revision=expected_revision,revision=expected_revision+1,
                source_claim_id=row['source_claim_id'],rationale=rationale,source_ids=row['source_ids'])))

def policy():
    with store.connect() as conn:
        return rows(conn.execute('SELECT * FROM local_policy WHERE id=1'))[0]

def update_policy(actor, payload):
    with store.connect() as conn:
        current = conn.execute('SELECT revision FROM local_policy WHERE id=1 FOR UPDATE').fetchone()[0]
        if payload['expected_revision'] != current: raise ValueError('Policy revision is stale')
        conn.execute('UPDATE local_policy SET revision=revision+1,inference_enabled=%s,daily_call_limit=%s,max_output_tokens=%s,central_config=%s::jsonb WHERE id=1',
            (payload['inference_enabled'],payload['daily_call_limit'],payload['max_output_tokens'],json.dumps(payload['central_config'])))
        return dict(revision=current+1,audit_receipt=audit(conn,actor,'policy.updated',payload))

def reserve_inference(actor):
    from .operational_policy import operational_policy
    limits=operational_policy()
    reconcile_inference(actor)
    with store.connect() as conn:
        current = rows(conn.execute('SELECT * FROM local_policy WHERE id=1 FOR UPDATE'))[0]
        if not current['inference_enabled']: raise PermissionError('Inference disabled by local administrator')
        count = conn.execute('SELECT nsai_daily_inference_count()').fetchone()[0]
        if count >= current['daily_call_limit']: raise ValueError('Daily inference call budget exhausted')
        personal=conn.execute("SELECT count(*) FROM inference_runs WHERE actor=%s AND created_at>=date_trunc('day',now() AT TIME ZONE 'UTC') AT TIME ZONE 'UTC'",(actor,)).fetchone()[0]
        if personal>=limits.generations_per_day:raise ValueError('Personal daily generation allowance exhausted')
        active=conn.execute("SELECT count(*) FROM inference_runs WHERE actor=%s AND state='reserved'",(actor,)).fetchone()[0]
        if active>=limits.generations_per_user:raise ValueError('Personal generation concurrency reached')
        if conn.execute('SELECT nsai_active_inference_count()').fetchone()[0]>=limits.gpu_jobs:
            raise ValueError('Global inference concurrency reached')
        run_id = uuid4().hex
        conn.execute("INSERT INTO inference_runs(id,actor,state) VALUES(%s,%s,'reserved')", (run_id,actor))
        return run_id,current['max_output_tokens']

def finish_inference(run_id, actor, details, failed=False):
    from .source_dependencies import collect_sources
    sources=collect_sources(details)
    with store.connect() as conn:
        record=conn.execute('SELECT actor,state,details FROM inference_runs WHERE id=%s FOR UPDATE',(run_id,)).fetchone()
        if not record:raise LookupError('Inference reservation not found')
        if record[0]!=actor:raise PermissionError('Inference reservation owner mismatch')
        if record[1]!='reserved':return record[2].get('audit_receipt')
        receipt=audit(conn,actor,'inference.failed' if failed else 'inference.completed',dict(run_id=run_id,**details))
        details=dict(details,audit_receipt=receipt)
        conn.execute('UPDATE inference_runs SET state=%s,details=%s::jsonb,source_ids=%s,provenance_complete=true WHERE id=%s', ('failed' if failed else 'completed',json.dumps(details),sources,run_id))
        return receipt

def reconcile_inference(actor,max_age_seconds=300):
    if type(max_age_seconds) is not int or not 180<=max_age_seconds<=86400:raise ValueError('Invalid lease age')
    with store.connect() as conn:
        records=rows(conn.execute("SELECT id,actor FROM inference_runs WHERE state='reserved' AND created_at<now()-(%s*interval '1 second') FOR UPDATE SKIP LOCKED",(max_age_seconds,)))
        for record in records:
            receipt=audit(conn,actor,'inference.abandoned',dict(run_id=record['id'],reservation_actor=record['actor']))
            conn.execute("UPDATE inference_runs SET state='failed',details=%s::jsonb,source_ids=ARRAY[]::text[],provenance_complete=true WHERE id=%s",(json.dumps(dict(reason='lease-expired',audit_receipt=receipt)),record['id']))
        return dict(reconciled=len(records),attempts_remain_charged=True)

def begin_invocation(actor,request_id,payload):
    if request_id is None:return None
    fingerprint=canonical_hash(payload)
    with store.connect() as conn:
        conn.execute('SELECT pg_advisory_xact_lock(878712)')
        existing=conn.execute("SELECT payload_sha256,state,response,created_at<now()-interval '15 minutes' FROM invocation_receipts WHERE actor=%s AND request_id=%s FOR UPDATE",(actor,request_id)).fetchone()
        if existing:
            if existing[0]!=fingerprint:raise ValueError('Idempotency key does not match request')
            if existing[1]=='completed':
                from .answer_support import require_current_response
                return require_current_response(existing[2])
            if existing[1]=='pending' and existing[3]:
                # Terminal failure is committed before reporting it to the caller.
                # Reusing this key never executes the operation a second time.
                conn.execute("UPDATE invocation_receipts SET state='failed',response=%s::jsonb,source_ids=ARRAY[]::text[],provenance_complete=true WHERE actor=%s AND request_id=%s AND state='pending'",
                    (json.dumps(dict(reason='invocation-lease-expired',retry_with_same_key=False,outcome='unknown; inspect related audit and inference receipts')),actor,request_id))
                conn.commit()
            raise ValueError('Request is pending or failed; inspect its receipt before starting a new request')
        inserted=conn.execute("INSERT INTO invocation_receipts(actor,request_id,payload_sha256,state) VALUES(%s,%s,%s,'pending') ON CONFLICT DO NOTHING",(actor,request_id,fingerprint)).rowcount
        if not inserted:raise LookupError('Invocation receipt unavailable')
    return None

def finish_invocation(actor,request_id,result,failed=False):
    if request_id is None:return
    encoded=json.dumps(result,ensure_ascii=False,allow_nan=False)
    if len(encoded.encode())>256000:raise ValueError('Invocation receipt exceeds budget')
    from .source_dependencies import stored_provenance
    sources,complete=stored_provenance(result)
    if failed:
        if set(result)-{'error_type','reason','retry_with_same_key','outcome'}:
            raise ValueError('Failure receipt must contain source-independent status only')
        complete=True
    with store.connect() as conn:
        conn.execute("UPDATE invocation_receipts SET state=%s,response=%s::jsonb,source_ids=%s,provenance_complete=%s WHERE actor=%s AND request_id=%s AND state='pending'",('failed' if failed else 'completed',encoded,sources,complete,actor,request_id))

def invocation_status(actor,request_id):
    with store.connect() as conn:
        result=rows(conn.execute('SELECT request_id,state,response,created_at FROM invocation_receipts WHERE actor=%s AND request_id=%s',(actor,request_id)))
    if not result:raise LookupError('Invocation receipt unavailable to this actor')
    from .answer_support import response_is_current,VERSION
    if result[0]['state']=='completed' and not response_is_current(result[0]['response']):
        result[0]['response']=None
        result[0]['response_withheld']='Stored completion requires current support validation; send the question as a new request'
        result[0]['required_support_policy_version']=VERSION
    return result[0]

def resource_usage():
    """Measured local usage, with missing observations explicit and no priced/ROI claims."""
    with store.connect() as conn:
        runs=rows(conn.execute("SELECT id,state,details,created_at FROM inference_runs WHERE created_at>=date_trunc('day',now() AT TIME ZONE 'UTC') AT TIME ZONE 'UTC' ORDER BY created_at"))
    completed=sum(r['state']=='completed' for r in runs)
    latency=[];tokens=[]
    for run in runs:
        details=run['details'];value=details.get('latency_ms')
        if type(value) is int and value>=0:latency.append(value)
        usage=details.get('usage')
        value=usage.get('completion_tokens') if isinstance(usage,dict) else None
        if type(value) is int and value>=0:tokens.append(value)
    return dict(period='current UTC day',attempts=len(runs),completed_inferences=completed,
        completed_is_verified_resolution=False,observed_latency_ms=sum(latency) if latency else None,
        latency_observations=len(latency),observed_completion_tokens=sum(tokens) if tokens else None,
        token_observations=len(tokens),financial_cost=None,verified_outcome_cost=None,
        unknown_denominator_policy='unknown; no fabricated zero or ROI',metric_version='local-resource/1',
        source_receipt_sha256=canonical_hash([dict(id=r['id'],state=r['state'],details=r['details']) for r in runs]))

def audit_report():
    with store.connect() as conn:
        records = rows(conn.execute('SELECT id,actor,event_type,details,previous_sha256,sha256,created_at FROM audit_events ORDER BY id'))
    previous = '0'*64
    valid = True
    rows_valid=True
    for record in records:
        body = {key:record[key] for key in ('actor','event_type','details','previous_sha256')}
        valid = valid and record['previous_sha256'] == previous and canonical_hash(body) == record['sha256']
        rows_valid=rows_valid and canonical_hash(body)==record['sha256']
        previous = record['sha256']
    # RLS can intentionally omit another actor's events. A scoped result cannot
    # attest global continuity, even when its visible hashes are well formed.
    identity=store.request_identity()
    scoped=identity is not None and identity.get('identity_kind')=='local-user'
    verdict=None if scoped or (rows_valid and not valid) else valid
    return dict(valid=verdict,count=len(records),head_sha256=previous,items=records[-100:],
        visible_row_hashes_valid=rows_valid,scope='authorized-subset' if scoped else 'legacy-visible-chain',
        limitation='Scoped visible events; global continuity requires an authorized owner-side audit. Local hashes are not external signatures.')
