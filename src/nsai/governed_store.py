"""Authenticated APIs call these transactional original NSAI assembly adapters."""
from datetime import datetime,timezone,timedelta
from dataclasses import asdict
import json
from . import store,workflow_store as w
from .assembly import AssemblyPlan,AssemblyNode,canonical_hash,strict_json
from .governance import ProposalRegistry
from .models import observe_statements

def persist(kind,actor,document_id,payload):
    if kind not in {'assembly','issues','proposal','extraction'}:raise ValueError('Unsupported record kind')
    payload=strict_json(json.dumps(payload,ensure_ascii=False,allow_nan=False),max_bytes=16*1024*1024,max_items=100000)
    from .source_dependencies import collect_sources
    sources=collect_sources(payload,required=[document_id])
    original,media=w.original_source(document_id)
    source=w.source(document_id)
    identifier=canonical_hash(dict(kind=kind,author=actor,document_id=document_id,source_sha256=source['original_sha256'],payload=payload))
    with store.connect() as conn:
        # The database serializes global accounting after RLS source checks;
        # an ignored duplicate consumes no additional storage or record budget.
        inserted=conn.execute('INSERT INTO governed_records(id,kind,author,document_id,source_sha256,payload,source_ids,provenance_complete) VALUES(%s,%s,%s,%s,%s,%s::jsonb,%s,true) ON CONFLICT DO NOTHING',(identifier,kind,actor,document_id,source['original_sha256'],json.dumps(payload,ensure_ascii=False),sources)).rowcount
        receipt=w.audit(conn,actor,'governed.'+kind+'.proposed',dict(record_id=identifier,document_id=document_id,source_ids=sources)) if inserted else None
    return dict(id=identifier,state='candidate',created=bool(inserted),authority_granted=False,audit_receipt=receipt,payload=payload)

def assemble(actor,document_id):
    source=w.source(document_id)
    original,media=w.original_source(document_id)
    # Assemble persisted extraction only. PDF interpretation belongs exclusively
    # to the isolated parser/OCR boundary, never the credential-bearing API.
    metadata=source.get('manifest',{}).get('documents',[{}])[0].get('metadata',{})
    with store.connect() as conn:
        chunks=w.rows(conn.execute('SELECT locator,text,sha256 FROM chunks WHERE document_id=%s ORDER BY id',(document_id,)))
    parsed=dict(original_sha256=source['original_sha256'],raw_text=source['raw_text'],
        parser_version=metadata.get('parser_version','legacy-unknown'),spans=metadata.get('spans',[]),
        chunks=metadata.get('chunks',chunks),pages=metadata.get('pages',[]),normalization_map=metadata.get('normalization_map',[]),
        complete=metadata.get('complete',media!='application/pdf'),warnings=metadata.get('warnings',[]))
    digest=source['original_sha256']
    plan=AssemblyPlan(tuple(AssemblyNode(name,op,deps,canonical_hash(dict(operator=op,version='1'))) for name,op,deps in [
        ('parse','parse',()),('normalize','normalize',('parse',)),('extract','extract',('normalize',)),('validate','validate',('extract',)),('index','index',('validate',)),('project','project',('index',))]))
    outputs=dict(parse=parsed,normalize=parsed.get('normalization_map',[]),extract=observe_statements(parsed['raw_text']),
        validate=dict(original_integrity=True,processing_complete=parsed['complete'],quality='unverified'),index=parsed['chunks'],
        project=dict(state='candidate',source_revision=source['revision'],source_sha256=digest,authority_granted=False))
    receipts={}
    for name in plan.order:
        node=plan.nodes[name]
        receipts[name]=plan.create_receipt(name,source_sha256=digest,output=outputs[name],dependencies={d:receipts[d] for d in node.dependencies},generation=1)
    for receipt in receipts.values():plan.require_fresh(receipt,source_sha256=digest,current=receipts)
    return persist('assembly',actor,document_id,dict(plan_version='1',outputs=outputs,receipts={k:asdict(v) for k,v in receipts.items()},execution_enabled=False))

def analyze_issue(actor,document_id):
    from .issue_assembly import build_engineering_flow
    source=w.source(document_id)
    w.original_source(document_id)
    with store.connect() as conn:
        spans=w.rows(conn.execute('SELECT locator,text FROM source_spans WHERE document_id=%s ORDER BY locator',(document_id,)))
    result=build_engineering_flow(document_id=document_id,revision=source['revision'],source_sha256=source['original_sha256'],spans=spans)
    return persist('issues',actor,document_id,result)

def propose(actor,document_id,capability,data):
    proposal=ProposalRegistry.propose(capability=capability,actor=actor,data=data)
    return persist('proposal',actor,document_id,dict(proposal=asdict(proposal),data=data))

def records(actor,reviewer=False,limit=25,offset=0):
    if not 1<=limit<=100 or not 0<=offset<=100000:raise ValueError('Invalid record page')
    with store.connect() as conn:
        return w.rows(conn.execute('SELECT g.id,g.kind,g.author,g.document_id,g.source_sha256,g.created_at,coalesce(r.decision,\'candidate\') AS state FROM governed_records g LEFT JOIN governed_reviews r ON r.record_id=g.id WHERE (%s OR g.author=%s) ORDER BY g.created_at DESC,g.id LIMIT %s OFFSET %s',(reviewer,actor,limit,offset)))

def record(actor,record_id,reviewer=False):
    with store.connect() as conn:
        result=w.rows(conn.execute("SELECT g.*,coalesce(r.decision,'candidate') AS state,"
            "CASE WHEN r.id IS NULL THEN NULL ELSE jsonb_build_object('id',r.id::text,'actor',r.actor,'decision',r.decision,'rationale',r.rationale,'created_at',r.created_at) END AS review,"
            "jsonb_build_object('id',d.id,'title',d.title,'revision',d.source_version,'original_sha256',d.original_sha256,'media_type',d.media_type) AS source,"
            "coalesce(d.source_bytes IS NOT NULL AND encode(sha256(d.source_bytes),'hex')=g.source_sha256 AND d.original_sha256=g.source_sha256,false) AS source_integrity_matches "
            "FROM governed_records g JOIN documents d ON d.id=g.document_id LEFT JOIN governed_reviews r ON r.record_id=g.id WHERE g.id=%s AND (%s OR g.author=%s)",(record_id,reviewer,actor)))
    if not result:raise LookupError('Record unavailable to this actor')
    value=result[0];identity=store.request_identity()
    value['can_review']=bool(identity and identity.get('role') in {'reviewer','admin'} and value['author']!=actor and value['review'] is None and value['source_integrity_matches'] and value['provenance_complete'] is True and value['document_id'] in value['source_ids'])
    value['authority_granted']=False
    return value

def review(actor,record_id,decision,rationale):
    if not isinstance(decision,str) or decision not in {'reviewed','rejected'} or not isinstance(rationale,str) or not 10<=len(rationale)<=2000 or not rationale.strip():raise ValueError('Invalid review')
    with store.connect() as conn:
        conn.execute('SELECT pg_advisory_xact_lock(878709)')
        record=conn.execute('SELECT author,document_id,source_sha256,source_ids,provenance_complete FROM governed_records WHERE id=%s',(record_id,)).fetchone()
        if not record:raise LookupError('Record not found')
        if record[0]==actor:raise PermissionError('Independent reviewer required')
        if conn.execute('SELECT 1 FROM governed_reviews WHERE record_id=%s',(record_id,)).fetchone():raise ValueError('Record already reviewed')
        if record[4] is not True or record[1] not in record[3]:raise LookupError('Complete source provenance required for review')
        from .source_dependencies import validate_sources
        validate_sources(conn,record[3])
        # Keep source integrity and record binding in this transaction's pool slot.
        source=conn.execute('SELECT source_bytes,original_sha256 FROM documents WHERE id=%s',(record[1],)).fetchone()
        if not source or source[0] is None:raise LookupError('Original source unavailable')
        original=bytes(source[0])
        import hashlib
        digest=hashlib.sha256(original).hexdigest()
        if digest!=source[1]:raise ValueError('Source integrity failure')
        if digest!=record[2]:raise ValueError('Stale source binding')
        conn.execute('INSERT INTO governed_reviews(record_id,actor,decision,rationale) VALUES(%s,%s,%s,%s)',(record_id,actor,decision,rationale))
        return dict(record_id=record_id,state=decision,authority_granted=False,audit_receipt=w.audit(conn,actor,'governed.reviewed',dict(record_id=record_id,document_id=record[1],source_ids=record[3],decision=decision,rationale=rationale)))

def stage_policy(actor,payload):
    if payload.get('central_config',{}).get('enabled') is not False:raise PermissionError('Central activation denied')
    current=w.policy()
    if current['revision']!=payload['expected_revision']:raise ValueError('Stale policy revision')
    identifier=canonical_hash(dict(actor=actor,payload=payload))
    with store.connect() as conn:
        conn.execute('SELECT pg_advisory_xact_lock(878710)')
        conn.execute("INSERT INTO policy_actions(id,requested_by,policy_revision,payload,state,expires_at) VALUES(%s,%s,%s,%s::jsonb,'pending',now()+interval '15 minutes') ON CONFLICT DO NOTHING",(identifier,actor,current['revision'],json.dumps(payload)))
        return dict(state='pending-independent-review',action_id=identifier,policy_unchanged=True,authority_granted=False)

def approve_policy(actor,action_id,approve):
    with store.connect() as conn:
        record=conn.execute('SELECT requested_by,policy_revision,payload,state,expires_at,receipt_sha256 FROM policy_actions WHERE id=%s FOR UPDATE',(action_id,)).fetchone()
        if not record:raise LookupError('Action not found')
        if record[0]==actor:raise PermissionError('Independent approval required')
        if record[3]!='pending':return dict(state=record[3],audit_receipt=record[5],idempotent=True)
        if record[4]<=datetime.now(timezone.utc):raise ValueError('Action expired')
        current=conn.execute('SELECT revision FROM local_policy WHERE id=1 FOR UPDATE').fetchone()[0]
        if current!=record[1]:raise ValueError('Approval binds a stale policy revision')
        payload=record[2]
        state='rejected'
        if approve:
            if payload['central_config']['enabled'] is not False:raise PermissionError('Central activation denied')
            conn.execute('UPDATE local_policy SET revision=revision+1,inference_enabled=%s,daily_call_limit=%s,max_output_tokens=%s,central_config=%s::jsonb WHERE id=1',(payload['inference_enabled'],payload['daily_call_limit'],payload['max_output_tokens'],json.dumps(payload['central_config'])))
            state='applied'
        receipt=w.audit(conn,actor,'policy.action.'+state,dict(action_id=action_id,requested_by=record[0],policy_revision=current))
        conn.execute('UPDATE policy_actions SET state=%s,approved_by=%s,receipt_sha256=%s WHERE id=%s',(state,actor,receipt,action_id))
        return dict(state=state,audit_receipt=receipt,individual_identity_step_up='not-commissioned-local-demo-role-token-only')

def pending_actions():
    with store.connect() as conn:
        return w.rows(conn.execute("SELECT id,requested_by,policy_revision,payload,state,expires_at FROM policy_actions ORDER BY created_at DESC LIMIT 25"))

def retention_dry_run():
    with store.connect() as conn:
        counts={name:conn.execute('SELECT count(*) FROM '+name).fetchone()[0] for name in ['documents','claims','sessions','session_messages','inference_runs','audit_events','governed_records']}
    return dict(counts=counts,database_bytes=None,count_scope='authorized rows only',delete_enabled=False,holds='all originals and audit events retained',state='inspection-only',automatic_cleanup=False)
