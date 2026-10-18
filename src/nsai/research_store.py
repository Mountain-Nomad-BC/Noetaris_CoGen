"""Transactional source-derived research artifacts; candidates never become canon here."""
import hashlib
import json
import re
from . import store


def artifact_hash(value):
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()
    if len(raw) > 16 * 1024 * 1024:
        raise ValueError('Research artifact exceeds 16 MiB')
    return hashlib.sha256(raw).hexdigest()


def build(document_id, revision, parsed):
    from .scientific_math import extract_math
    from .knowledge import assemble_knowledge, memory_projection
    formulas = extract_math(parsed, document_id, revision)
    knowledge = assemble_knowledge(document_id, revision, parsed['original_sha256'], parsed['spans'],
                                   formula_nodes=formulas['records'])
    knowledge['extraction_coverage'] = dict(complete=parsed['complete'], pages=parsed['pages'],
        quality_verified=False, formula_detection_exhaustive=False)
    if not knowledge['source_processing_complete'] or not formulas['processing_complete']:
        raise ValueError('Structured research assembly exceeded its complete-processing budget')
    knowledge['memory_projection'] = memory_projection(knowledge, max_bytes=4096, max_items=6)
    knowledge['graph_sha256'] = artifact_hash({k:v for k,v in knowledge.items() if k!='graph_sha256'})
    return dict(knowledge=knowledge, formulas=formulas)


def persist(conn, document_id, revision, digest, artifacts):
    """Caller owns source transaction: source and structured artifacts commit together."""
    checksum = artifact_hash(artifacts)
    previous = conn.execute('SELECT artifact_sha256 FROM document_knowledge WHERE document_id=%s', (document_id,)).fetchone()
    if previous:
        if previous[0] != checksum:
            raise ValueError('Existing immutable research artifact differs; use an explicit new generation')
        return checksum
    from .source_dependencies import collect_sources,RESEARCH_VISIT_BUDGET
    sources=collect_sources(artifacts,required=[document_id],conn=conn,traversal_budget=RESEARCH_VISIT_BUDGET)
    conn.execute('INSERT INTO document_knowledge(document_id,source_sha256,revision,knowledge,formulas,artifact_sha256,source_ids,provenance_complete) '
                 'VALUES(%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s,true)',
                 (document_id, digest, revision, json.dumps(artifacts['knowledge'], ensure_ascii=False),
                  json.dumps(artifacts['formulas'], ensure_ascii=False), checksum,sources))
    return checksum


def get(document_id, *, conn=None, include_staged=False):
    from .workflow_store import rows
    if conn is None:
        with store.connect() as owned:return get(document_id,conn=owned,include_staged=include_staged)
    identity=store.request_identity()
    worker=identity is not None and identity.get('identity_kind')=='source-job'
    if include_staged or worker:
        if not conn.execute('SELECT nsai_source_is_owner(%s) OR nsai_legacy_context()',
                            (document_id,)).fetchone()[0]:raise LookupError('Source index unavailable')
    elif not conn.execute('SELECT nsai_index_source_readable(%s)',(document_id,)).fetchone()[0]:
        raise LookupError('Source index unavailable')
    result = rows(conn.execute('SELECT k.*,d.original_sha256 FROM document_knowledge k JOIN documents d ON d.id=k.document_id WHERE k.document_id=%s', (document_id,)))
    if not result:
        raise LookupError('Research artifacts unavailable; source requires ingestion with the research pipeline')
    value = result[0]
    if value['source_sha256'] != value['original_sha256'] or artifact_hash({k: value[k] for k in ['knowledge', 'formulas']}) != value['artifact_sha256']:
        raise ValueError('Research artifact integrity mismatch')
    return value


def document_units(document_id):
    """Versioned read-only projection; existing immutable knowledge is not rewritten."""
    from .document_units import assemble_document_units
    artifact = get(document_id)
    spans = [dict(locator=node['locator'], text=node['text'], page=node.get('page'))
             for node in artifact['knowledge']['nodes'] if node['kind']=='source_span']
    result = assemble_document_units(document_id,artifact['revision'],artifact['source_sha256'],spans)
    return dict(projection=result, parent_artifact_sha256=artifact['artifact_sha256'],
                persistence='derived-on-read; original knowledge unchanged', authority_granted=False)


def put_embeddings(document_id, vectors, model_identity, coverage, actor, *, conn=None):
    from .knowledge import attach_embeddings
    from .workflow_store import audit
    if (not isinstance(vectors,dict) or not vectors or len(vectors)>10000
        or not isinstance(coverage,dict) or set(vectors)!=set(coverage)
        or not isinstance(model_identity,dict) or not isinstance(model_identity.get('name'),str)
        or not re.fullmatch('[a-f0-9]{64}',model_identity.get('sha256',''))
        or not re.fullmatch('[a-f0-9]{40}',model_identity.get('revision',''))
        or model_identity.get('dimension')!=384
        or model_identity.get('pooling')!='token-mean-overlap-compensated-special-mean'):
        raise ValueError('Invalid complete embedding request')
    if conn is None:
        with store.connect() as owned:
            return put_embeddings(document_id,vectors,model_identity,coverage,actor,conn=owned)
    artifact = get(document_id,conn=conn,include_staged=True)
    graph = attach_embeddings(artifact['knowledge'], vectors, model_identity, coverage)
    normalized={record['node_id']:record['vector'] for record in graph['embeddings']['records']}
    payload = dict(model_identity=model_identity, vectors=normalized, coverage=coverage,
                   source_sha256=artifact['source_sha256'], knowledge_sha256=artifact['artifact_sha256'])
    checksum = artifact_hash(payload)
    model_sha = model_identity['sha256']
    if not re.fullmatch(r'[a-f0-9]{64}', model_sha):
        raise ValueError('Invalid model identity')
    conn.execute('SELECT pg_advisory_xact_lock(878712)')
    old = conn.execute('SELECT artifact_sha256 FROM knowledge_embeddings WHERE document_id=%s AND model_sha256=%s', (document_id, model_sha)).fetchone()
    if old:
        if old[0] != checksum:
            raise ValueError('Immutable embedding generation already exists with different content')
        return dict(created=False, artifact_sha256=checksum, authority_granted=False)
    # The database trigger accounts for every owner's committed canonical bytes.
    # A request/job-scoped SELECT cannot enforce a global storage budget.
    from .source_dependencies import collect_sources,RESEARCH_VISIT_BUDGET
    sources=collect_sources(artifact,required=[document_id],conn=conn,traversal_budget=RESEARCH_VISIT_BUDGET)
    conn.execute('INSERT INTO knowledge_embeddings(document_id,model_sha256,artifact_sha256,payload,source_ids,provenance_complete) VALUES(%s,%s,%s,%s::jsonb,%s,true)',
                 (document_id, model_sha, checksum, json.dumps(payload, allow_nan=False),sources))
    receipt = audit(conn, actor, 'knowledge.embedded', dict(document_id=document_id, model_sha256=model_sha, artifact_sha256=checksum))
    return dict(created=True, artifact_sha256=checksum, authority_granted=False, audit_receipt=receipt)


def embedded_graph(document_id, model_sha256):
    from .knowledge import attach_embeddings
    artifact = get(document_id)
    with store.connect() as conn:
        row = conn.execute('SELECT payload,artifact_sha256 FROM knowledge_embeddings WHERE document_id=%s AND model_sha256=%s', (document_id, model_sha256)).fetchone()
    if not row:
        raise LookupError('Requested source/model embedding generation unavailable')
    payload = row[0]
    if artifact_hash(payload) != row[1] or payload['knowledge_sha256'] != artifact['artifact_sha256'] or payload['source_sha256'] != artifact['source_sha256']:
        raise ValueError('Stale or corrupt embedding generation')
    return attach_embeddings(artifact['knowledge'], payload['vectors'], payload['model_identity'], payload['coverage'])


def put_supplement(document_id, payload, actor):
    """Stage an immutable separately represented extraction, with a reviewable descriptor."""
    from .knowledge import attach_embeddings
    from .workflow_store import original_source, audit
    from .assembly import canonical_hash
    original, _ = original_source(document_id)
    main=get(document_id)
    digest=hashlib.sha256(original).hexdigest()
    if payload.get('schema_version')!='nsai.research-supplement/1' or payload.get('kind') not in {'ocr','author_math'}:
        raise ValueError('Unsupported research supplement schema')
    if payload.get('document_id')!=document_id or payload.get('source_sha256')!=digest:
        raise ValueError('Supplement original source binding mismatch')
    graph=payload.get('knowledge');extraction=payload['extraction']
    memory=payload.get('memory')
    if memory is not None and (memory.get('canon')!=[] or memory.get('authority_granted') is not False):
        raise ValueError('Supplement evidence memory cannot promote canon')
    expected=dict(document_id=document_id,revision=main['revision'],source_sha256=digest)
    if graph is not None:
        if graph.get('source')!=expected or graph.get('authority_granted') is not False or graph.get('source_processing_complete') is not True:
            raise ValueError('Invalid supplement knowledge identity or authority')
        if any(n.get('source')!=expected or n.get('authority_granted') is not False or n.get('state')!='candidate' for n in graph['nodes']):
            raise ValueError('Supplement knowledge cannot grant authority')
        if any(edge.get('provenance')!=expected or edge.get('authority_granted') is not False or edge.get('state')!='candidate' for edge in graph['edges']):
            raise ValueError('Supplement edges cannot grant authority')
        if graph.get('extraction_evidence_sha256')!=artifact_hash(extraction):
            raise ValueError('Supplement extraction/graph byte-content mismatch')
        attach_embeddings(graph,**payload['embeddings'])
    elif payload.get('embeddings') is not None:
        raise ValueError('Missing supplement graph cannot have semantic embeddings')
    if payload['kind']=='ocr':
        from .ingestion import validate_parsed_source
        validate_parsed_source(original,extraction)
    else:
        if (extraction.get('pdf_sha256')!=digest or extraction.get('document_id')!=document_id or extraction.get('revision')!=main['revision']
            or extraction.get('source_kind')!='author_source_tex_not_pdf' or extraction.get('authority_granted') is not False
            or any(r.get('source_sha256')!=digest or r.get('generated_execution') is not False or r.get('evaluation')!='not_attempted' for r in extraction.get('records',[]))):
            raise ValueError('Author source association or candidate authority mismatch')
    identifier=artifact_hash(payload)
    descriptor=dict(schema_version='nsai.research-supplement-review/1',supplement_id=identifier,
                    kind=payload['kind'],state='candidate',authority_granted=False,
                    extraction_quality_verified=False,source_custody='Inspect source archive/OCR receipts; submission alone is not independent validation')
    review_id=canonical_hash(dict(kind='extraction',author=actor,document_id=document_id,source_sha256=digest,payload=descriptor))
    with store.connect() as conn:
        conn.execute('SELECT pg_advisory_xact_lock(878713)')
        existing=conn.execute('SELECT review_record_id FROM research_supplements WHERE id=%s',(identifier,)).fetchone()
        if existing:
            return dict(id=identifier,created=False,review_record_id=existing[0],authority_granted=False)
        conn.execute('SELECT pg_advisory_xact_lock(878711)')
        count,review_bytes=conn.execute('SELECT count(*),coalesce(sum(octet_length(payload::text)),0) FROM governed_records').fetchone()
        if conn.execute('SELECT count(*) FROM research_supplements').fetchone()[0]>=2000 or count>=2000 or review_bytes+len(json.dumps(descriptor).encode())>128*1024*1024:
            raise ValueError('Research supplement/review-record count budget reached')
        size=conn.execute('SELECT coalesce(sum(octet_length(payload::text)),0) FROM research_supplements').fetchone()[0]
        encoded=json.dumps(payload,ensure_ascii=False,allow_nan=False)
        if size+len(encoded.encode())>128*1024*1024:raise ValueError('Supplement storage budget reached')
        from .source_dependencies import collect_sources,RESEARCH_VISIT_BUDGET
        sources=collect_sources(payload,required=[document_id],conn=conn,traversal_budget=RESEARCH_VISIT_BUDGET)
        conn.execute("INSERT INTO governed_records(id,kind,author,document_id,source_sha256,payload,source_ids,provenance_complete) VALUES(%s,'extraction',%s,%s,%s,%s::jsonb,%s,true) ON CONFLICT DO NOTHING",
            (review_id,actor,document_id,digest,json.dumps(descriptor),sources))
        conn.execute('INSERT INTO research_supplements(id,document_id,kind,source_sha256,review_record_id,payload,author,source_ids,provenance_complete) VALUES(%s,%s,%s,%s,%s,%s::jsonb,%s,%s,true)',
            (identifier,document_id,payload['kind'],digest,review_id,encoded,actor,sources))
        receipt=audit(conn,actor,'knowledge.supplement.proposed',dict(document_id=document_id,supplement_id=identifier,review_record_id=review_id))
    return dict(id=identifier,created=True,review_record_id=review_id,authority_granted=False,audit_receipt=receipt)


def supplements(document_id):
    from .workflow_store import rows
    with store.connect() as conn:
        result=rows(conn.execute("SELECT s.id,s.kind,s.source_sha256,s.payload,s.created_at,s.review_record_id,coalesce(r.decision,'candidate') AS review_state "
            "FROM research_supplements s LEFT JOIN governed_reviews r ON r.record_id=s.review_record_id "
            "WHERE s.document_id=%s ORDER BY s.created_at,s.id",(document_id,)))
    for row in result:
        if artifact_hash(row['payload'])!=row['id']:raise ValueError('Supplement content digest mismatch')
    return result


def search(vector, model_sha256, document_ids, limit=12, include_supplements=False):
    from .knowledge import cosine_search
    if type(include_supplements) is not bool or not 1 <= len(document_ids) <= 20 or len(set(document_ids)) != len(document_ids) or not 1 <= limit <= 20:
        raise ValueError('Select 1–20 distinct documents and a bounded result count')
    hits = []
    for document_id in document_ids:
        hits.extend(cosine_search(embedded_graph(document_id, model_sha256), vector, model_sha256=model_sha256, top_k=limit))
        if include_supplements:
            from .knowledge import attach_embeddings
            for item in supplements(document_id):
                if item['review_state']=='rejected':continue
                payload=item['payload']
                if not payload.get('knowledge') or not payload.get('embeddings'):continue
                if payload['embeddings']['model_identity']['sha256']!=model_sha256:continue
                graph=attach_embeddings(payload['knowledge'],**payload['embeddings'])
                for hit in cosine_search(graph,vector,model_sha256=model_sha256,top_k=limit):
                    hit.update(extraction_kind=item['kind'],supplement_id=item['id'],review_state=item['review_state'],quality_verified=False)
                    hits.append(hit)
    hits.sort(key=lambda value: (-value['score'], value['id']))
    return dict(items=hits[:limit], matching_passages_returned=len(hits[:limit]),
                method='pretrained-semantic-cosine', exhaustive_answer=False, authority_granted=False)


def memory_candidates(document_ids, question='', revision=None, pages=None, max_bytes=2400):
    """Bounded evidence memory, separate from independently reviewed canon."""
    if not document_ids:
        return dict(items=[], reason='Explicit source selection required', authority_granted=False)
    terms = set(re.findall(r'\w+', question.casefold()))
    candidates = []
    for document_id in document_ids:
        try:
            artifact = get(document_id)
        except LookupError:
            continue
        if revision is not None and artifact['revision'] != revision:
            continue
        for node in artifact['knowledge']['nodes']:
            if node.get('kind') != 'passage':
                continue
            if pages and node.get('page') not in pages:
                continue
            text = node['text']
            score = len(terms & set(re.findall(r'\w+', text.casefold())))
            if terms and not score:
                continue
            candidates.append((score, node))
    candidates.sort(key=lambda item: (-item[0], item[1]['id']))
    result = dict(items=[], state='source-observation-candidates', canon=False, authority_granted=False)
    for _, node in candidates:
        entry = {key: node[key] for key in ['id', 'text', 'locator']}
        entry['text']=node['text'][:300]
        entry['excerpt_omitted_characters']=len(node['text'])-len(entry['text'])
        segments=[];cursor=0
        for segment in node.get('source_segments',[]):
            if cursor>=len(entry['text']):break
            count=min(len(segment['text']),len(entry['text'])-cursor)
            segments.append(dict(locator=segment['locator'],char_start=segment['char_start'],char_end=segment['char_start']+count))
            cursor+=len(segment['text'])+1
        entry.update(document_id=node.get('document_id'), source_sha256=node.get('source_sha256'),
                     source_segments=segments, review_required=True)
        trial = dict(result, items=result['items'] + [entry])
        if len(json.dumps(trial, ensure_ascii=False).encode()) > max_bytes:
            continue
        result = trial
        if len(result['items']) >= 6:
            break
    return result
