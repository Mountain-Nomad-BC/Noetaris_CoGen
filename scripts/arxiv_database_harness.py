"""Executed only inside an owned candidate container by qualify_arxiv_database.py."""
from pathlib import Path
import hashlib
import json
import os
from fastapi.testclient import TestClient
from nsai import store,workflow_store as w,research_store as research
from nsai.ingestion import validate_parsed_source
from nsai.api import app


def run():
    manifest=json.loads(Path('/corpus/manifest.json').read_text());checks=[]
    supplement_manifest=Path(os.environ['NSAI_CORPUS_ENRICHMENT']) if os.getenv('NSAI_CORPUS_ENRICHMENT') else None
    enrichment=json.loads(supplement_manifest.read_bytes()) if supplement_manifest else None
    supplemental={p['document_id']:p for p in enrichment['papers']} if enrichment else {}
    def check(name,value):
        checks.append(dict(name=name,pass_=bool(value)))
        if not value:raise AssertionError(name)
    def artifact(folder,row,key):
        item=row['files'][key];raw=(folder/item['path']).read_bytes()
        check(row['document_id']+':'+key+' bytes',hashlib.sha256(raw).hexdigest()==item['sha256'])
        return json.loads(raw) if key!='original' else raw
    operator={'Authorization':'Bearer '+Path('/tmp/operator').read_text()}
    viewer={'Authorization':'Bearer '+Path('/tmp/viewer').read_text()}
    client=TestClient(app)
    check('unauthenticated knowledge denied',client.get('/v1/knowledge/'+'a'*32).status_code==401)
    # Force the new structured stage to fail after source rows are written: all must roll back.
    from unittest.mock import patch
    from nsai.ingestion import parse_source
    atomic=b'If a transaction fails, this research source must not be retained.'
    atomic_id=hashlib.sha256(('atomic-test:'+hashlib.sha256(atomic).hexdigest()).encode()).hexdigest()[:32]
    with patch('nsai.research_store.persist',side_effect=ValueError('owned atomicity probe')):
        try:w.persist_source('Atomicity probe','atomic-test',atomic,parse_source(atomic,'source.txt'),'local-operator')
        except ValueError:pass
        else:raise AssertionError('Expected structured-stage rollback')
    with store.connect() as conn:
        check('structured failure rolls back original spans chunks and audit',
            all(conn.execute('SELECT count(*) FROM '+name+' WHERE '+column+'=%s',(atomic_id,)).fetchone()[0]==0
                for name,column in [('documents','id'),('source_spans','document_id'),('chunks','document_id'),('document_knowledge','document_id')])
            and conn.execute('SELECT count(*) FROM audit_events').fetchone()[0]==0)
    for row in manifest['papers']:
        identifier=row['document_id'];folder=Path('/corpus')/identifier
        original=artifact(folder,row,'original');parsed=artifact(folder,row,'parsed')
        validate_parsed_source(original,parsed)
        saved=w.persist_source(row['title'],row['revision'],original,parsed,'local-operator')
        check(identifier+':actual transactional source+knowledge',saved['created'] and saved['document_id']==identifier and saved['research_artifact_sha256']==row['artifact_sha256'])
        repeated=w.persist_source(row['title'],row['revision'],original,parsed,'local-operator')
        check(identifier+':idempotent original+artifacts',repeated['created'] is False)
        response=client.get('/v1/knowledge/'+identifier,headers=viewer)
        check(identifier+':authenticated knowledge API',response.status_code==200 and response.json()['artifact_sha256']==row['artifact_sha256'])
        units=client.get('/v1/knowledge/'+identifier+'/units',headers=viewer)
        check(identifier+':authenticated versioned document units',units.status_code==200 and units.json()['parent_artifact_sha256']==row['artifact_sha256'])
        projected=units.json()['projection']
        check(identifier+':document units exact persisted source coverage',
            projected['processing_complete'] and len(projected['units'])==len(parsed['spans'])
            and {u['locator']:u['text'] for u in projected['units']}=={s['locator']:s['text'] for s in parsed['spans']}
            and all(u['authority_granted'] is False and u['quality_verified'] is False for u in projected['units']))
        check(identifier+':anonymous unit projection denied',client.get('/v1/knowledge/'+identifier+'/units').status_code==401)
        formulas=client.get('/v1/knowledge/'+identifier+'/formulas',headers=viewer)
        check(identifier+':separate formula API',formulas.status_code==200 and formulas.json()==artifact(folder,row,'formulas'))
        original_response=client.get('/v1/sources/'+identifier+'/original',headers=viewer)
        check(identifier+':original PDF roundtrip',original_response.status_code==200 and original_response.content==original)
        embeddings=artifact(folder,row,'embeddings')
        added=research.put_embeddings(identifier,**embeddings,actor='local-operator')
        check(identifier+':actual semantic persistence',added['created'])
        check(identifier+':idempotent semantic generation',research.put_embeddings(identifier,**embeddings,actor='local-operator')['created'] is False)
        first=next(iter(embeddings['vectors']));vector=embeddings['vectors'][first]
        result=client.post('/v1/knowledge/semantic-search',headers=viewer,json=dict(vector=vector,model_sha256=embeddings['model_identity']['sha256'],document_ids=[identifier],limit=3))
        check(identifier+':semantic HTTP source/model scope',result.status_code==200 and result.json()['items'][0]['id']==first and result.json()['items'][0]['score']>.99999)
        check(identifier+':viewer embedding write denied',client.post('/v1/knowledge/'+identifier+'/embeddings',headers=viewer,json=dict(vectors={},model_identity={},coverage={})).status_code==403)
        # Scope a real chat/memory exchange to an existing source phrase, no model/API spend.
        graph=artifact(folder,row,'knowledge');passage=next(n for n in graph['nodes'] if n['kind']=='passage')
        import nsai.api as api
        observed_errors=[];translate=api.translate_error
        def capture_error(error):
            observed_errors.append(dict(type=type(error).__name__,message=str(error)[:500]))
            return translate(error)
        with patch('nsai.api.translate_error',side_effect=capture_error):
            response=client.post('/v1/chat',headers=operator,json=dict(question=passage['text'][:120],document_ids=[identifier]))
        if response.status_code!=200:
            if observed_errors:raise AssertionError('Owned chat errors: '+str(observed_errors))
            # Diagnose the owned workflow directly; the public route intentionally hides internals.
            import nsai.api as api
            def raw_error(error):raise error
            with patch('nsai.api.translate_error',side_effect=raw_error):
                api.chat(api.Question(question=passage['text'][:120],document_ids=[identifier]),dict(actor='local-operator'))
            raise AssertionError('Owned chat failed: '+str(response.status_code)+' '+str(response.json())[:300])
        check(identifier+':source-selected evidence memory',response.status_code==200 and 'research_candidates' in response.json()['memory'] and response.json()['answer_verified'] is False)
        memory=response.json()['memory']
        check(identifier+':candidate memory source purity',all(item['document_id']==identifier for item in memory['research_candidates']['items']) and memory['canon']==[])
        check(identifier+':nonempty bounded research memory',bool(memory['research_candidates']['items']) and len(json.dumps(memory['research_candidates'],ensure_ascii=False).encode())<=2400)
        check(identifier+':formula candidate provenance',all(f['source_sha256']==row['source_sha256'] and f['evaluation']=='not_attempted' for f in formulas.json()['records']))
        for supplement in supplemental.get(identifier,{}).get('supplements',[]):
            location=supplement_manifest.parent/identifier/supplement['folder']
            def read_part(entry):
                raw=(location/entry['path']).read_bytes()
                check(identifier+':supplement file bytes',hashlib.sha256(raw).hexdigest()==entry['sha256'])
                return json.loads(raw)
            parts=supplement.get('files') or {}
            payload=dict(schema_version='nsai.research-supplement/1',document_id=identifier,source_sha256=row['source_sha256'],kind=supplement['kind'],
                         extraction=read_part(supplement['extraction']),knowledge=read_part(parts['knowledge']) if parts else None,
                         embeddings=read_part(parts['embeddings']) if parts else None,memory=read_part(parts['memory']) if parts else None)
            saved=research.put_supplement(identifier,payload,'local-operator')
            check(identifier+':'+supplement['kind']+' durable candidate supplement',saved['created'] and saved['authority_granted'] is False)
            check(identifier+':'+supplement['kind']+' idempotent source supplement',research.put_supplement(identifier,payload,'local-operator')['created'] is False)
            repeated_actor=research.put_supplement(identifier,payload,'local-reviewer')
            check(identifier+':supplement duplicate actor preserves original review binding',
                repeated_actor['created'] is False and repeated_actor['review_record_id']==saved['review_record_id'])
            with store.connect() as conn:
                linked=conn.execute('SELECT s.id,s.document_id,s.source_sha256,s.kind,s.author,s.review_record_id,'
                    'g.kind,g.author,g.document_id,g.source_sha256,g.payload FROM research_supplements s '
                    'JOIN governed_records g ON g.id=s.review_record_id WHERE s.id=%s',(saved['id'],)).fetchall()
            check(identifier+':one exact supplement review descriptor',len(linked)==1)
            link=linked[0];descriptor=link[10]
            check(identifier+':review descriptor source author kind lineage',
                link[0]==saved['id'] and link[1]==link[8]==identifier and link[2]==link[9]==row['source_sha256']
                and link[3]==supplement['kind'] and link[4]==link[7]=='local-operator' and link[6]=='extraction'
                and link[5]==saved['review_record_id'])
            check(identifier+':review descriptor cannot confer extraction authority',
                descriptor['schema_version']=='nsai.research-supplement-review/1' and descriptor['supplement_id']==saved['id']
                and descriptor['kind']==supplement['kind'] and descriptor['state']=='candidate'
                and descriptor['authority_granted'] is False and descriptor['extraction_quality_verified'] is False)
            from nsai import governed_store as governed
            try:governed.review('local-operator',saved['review_record_id'],'reviewed','Owned review-independence probe')
            except PermissionError:independence=True
            else:independence=False
            check(identifier+':supplement submitter cannot review own descriptor',independence)
            if parts:
                first=next(iter(payload['embeddings']['vectors']))
                found=client.post('/v1/knowledge/semantic-search',headers=viewer,json=dict(vector=payload['embeddings']['vectors'][first],model_sha256=payload['embeddings']['model_identity']['sha256'],document_ids=[identifier],limit=3,include_supplements=True))
                check(identifier+':supplement semantic HTTP source identity',found.status_code==200 and any(h['id']==first and h.get('supplement_id')==saved['id'] for h in found.json()['items']))
        if identifier in supplemental:
            response=client.get('/v1/knowledge/'+identifier+'/supplements',headers=viewer)
            check(identifier+':authenticated separate extraction API',response.status_code==200 and len(response.json()['items'])==len(supplemental[identifier]['supplements']))
    audit=w.audit_report();check('append-only audit chain',audit['valid'])
    denied=False
    try:
        with store.connect() as conn:conn.execute('UPDATE document_knowledge SET revision=revision')
    except Exception as error:
        denied=type(error).__name__=='InsufficientPrivilege'
    check('runtime role cannot rewrite structured source evidence',denied)
    with store.connect() as conn:
        counts={name:conn.execute('SELECT count(*) FROM '+name).fetchone()[0] for name in ['documents','document_knowledge','knowledge_embeddings','research_supplements','governed_records','claims','audit_events','sessions']}
        check('all originals structured artifacts and semantic generations persisted',counts['documents']==counts['document_knowledge']==counts['knowledge_embeddings']==len(manifest['papers']))
        check('no research auto-promoted to reviewed canon',conn.execute("SELECT count(*) FROM claims WHERE status='verified'").fetchone()[0]==0)
        check('no model inference consumed',conn.execute('SELECT count(*) FROM inference_runs').fetchone()[0]==0)
    return dict(status='PASS_SCOPED',checks=checks,counts=counts,source_manifest_sha256=hashlib.sha256(Path('/corpus/manifest.json').read_bytes()).hexdigest(),
        scope='Real owned PostgreSQL+candidate store/TestClient APIs. Semantic exact-quote identity is a custody check, not independent relevance accuracy.')


if __name__=='__main__':print(json.dumps(run(),allow_nan=False))
