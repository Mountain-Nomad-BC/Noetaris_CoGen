"""Original thirteen-document lexical limit qualification against PostgreSQL."""
import json,os,secrets,tempfile
from pathlib import Path
from nsai import store,workflow_store as w

def main():
    documents=[]
    for i in range(13):
        text=f'Unit-{i} maximum operating temperature is 75 C.\nIndependent synthetic label {i}.'
        documents.append(store.store_document('Synthetic retrieval source '+str(i),text,'1','local-operator')['document_id'])
    cases=[]
    def run(name,limit=12,expected_returned=12,expected_lower=13,expected_total=None,**scope):
        hits=w.retrieve('maximum temperature',limit,**scope);coverage=hits.coverage
        good=len(hits)==expected_returned and coverage['matching_chunks_lower_bound']==expected_lower and coverage['total_matching_chunks']==expected_total and coverage['additional_matches_exist']==(expected_total is None) and coverage['omitted_chunks_at_least']==max(0,expected_lower-limit)
        cases.append(dict(name=name,pass_=good,coverage=coverage,returned_ids=[h['id'] for h in hits]));return hits
    limited=run('default-thirteen-matches-truncated')
    complete=run('explicit-larger-limit-exact-total',20,13,13,13)
    cases.append(dict(name='ranking-and-order-preserved',pass_=[h['id'] for h in limited]==[h['id'] for h in complete[:12]]))
    run('smaller-limit-lower-bound-only',5,5,6,None)
    run('selected-document-exact-one',12,1,1,1,document_ids=[documents[0]])
    run('wrong-revision-exact-zero',12,0,0,0,document_ids=[documents[0]],revision='99')
    run('nonpdf-page-scope-exact-zero',12,0,0,0,document_ids=[documents[0]],pages=[1])
    from fastapi.testclient import TestClient
    with tempfile.TemporaryDirectory() as directory:
        token=secrets.token_hex(32);path=Path(directory)/'role.txt';path.write_text(token);os.environ['NSAI_API_TOKEN_FILE']=str(path)
        from nsai.api import app
        with TestClient(app) as client:
            response=client.post('/v1/chat',headers={'Authorization':'Bearer '+token},json=dict(question='maximum temperature'))
            body=response.json();coverage=body.get('retrieval_coverage',{})
            cases.append(dict(name='public-chat-truncation-marker-and-receipt',pass_=response.status_code==200 and len(body.get('citations',[]))==12 and body.get('answer','').startswith('RETRIEVAL LIMIT:') and coverage.get('additional_matches_exist') is True and coverage.get('matching_chunks_lower_bound')==13 and coverage.get('total_matching_chunks') is None,status=response.status_code,body=body))
    print(json.dumps(dict(all_pass=all(c['pass_'] for c in cases),cases=cases,documents=13,model_calls=0,scope='actual production retrieval + source persistence on synthetic owned PostgreSQL')))
    return 0 if all(c['pass_'] for c in cases) else 1

if __name__=='__main__':raise SystemExit(main())
