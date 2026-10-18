"""Original source/page/revision memory contract against actual PostgreSQL."""
from io import BytesIO
import inspect
import json
import os,secrets,tempfile
from pathlib import Path
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject,NameObject,DecodedStreamObject
from nsai import store,workflow_store as w
from nsai.ingestion import parse_source

def pdf(values):
    writer=PdfWriter()
    for value in values:
        page=writer.add_blank_page(width=612,height=792)
        font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
        page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):writer._add_object(font)})})
        text=DecodedStreamObject();text.set_data(('BT /F1 12 Tf 72 720 Td (Pump-X maximum operating temperature is '+str(value)+' C.) Tj ET').encode())
        page[NameObject('/Contents')]=writer._add_object(text)
    out=BytesIO();writer.write(out);return out.getvalue()

def main():
    from semantic_fixture_helpers import configure_authority,publish_pending
    configure_authority()
    docs=[]
    for revision,values in [('1',[75,95]),('2',[85,105])]:
        original=pdf(values);docs.append(w.persist_source('Original synthetic memory PDF',revision,original,parse_source(original,'memory.pdf'),'local-operator')['document_id'])
    publish_pending()  # Scope mechanics use synthetic vectors, not model-quality evidence.
    claims=store.all_claims();target=next(c for c in claims if c['document_id']==docs[0] and c['locator'].startswith('page:1:'))
    with store.connect() as c:
        c.execute("UPDATE claims SET status='verified',reviewed_by='independent-synthetic-reviewer'")
        c.execute("INSERT INTO learning_proposals(id,author,source_claim_id,reflection,state,created_at) VALUES('target-reflection','local-operator',%s,'Relevant source-page reflection','reviewed',now()-interval '1 minute')",(target['id'],))
        other=next(v for v in claims if v['document_id']==docs[1])
        for i in range(9):c.execute("INSERT INTO learning_proposals(id,author,source_claim_id,reflection,state) VALUES(%s,'local-operator',%s,'Unrelated newer reflection','reviewed')",('other-'+str(i),other['id']))
    sid=w.session('local-operator')
    w.save_exchange(sid,'Prior private working context',dict(answer='Prior private answer',mode='synthetic',citations=[]),'local-operator')
    cases=[]
    def run(name,kwargs,expected_ids,expected_reflections=None):
        supported='pages' in inspect.signature(w.memory_context).parameters
        actual_kwargs=kwargs if supported else {k:v for k,v in kwargs.items() if k=='document_ids'}
        result=w.memory_context('local-operator',sid,'maximum temperature',**actual_kwargs)
        ids={c['id'] for c in result['canon']};refs={r['id'] for r in result['reflection']}
        ok=ids==set(expected_ids) and not result['working']
        if expected_reflections is not None:ok &= refs==set(expected_reflections)
        cases.append(dict(name=name,pass_=ok,expected_claims=sorted(expected_ids),actual_claims=sorted(ids),reflections=sorted(refs),hypotheses=result['hypotheses'],scope=result.get('source_scope'),signature_supports_scope=supported))
    run('exact-document-revision-page',dict(document_ids=[docs[0]],revision='1',pages=[1]),[target['id']],['target-reflection'])
    run('wrong-revision-fails-closed',dict(document_ids=[docs[0]],revision='2',pages=[1]),[],[])
    run('wrong-page-fails-closed',dict(document_ids=[docs[0]],revision='1',pages=[99]),[],[])
    page2=next(c for c in claims if c['document_id']==docs[0] and c['locator'].startswith('page:2:'))
    run('second-page-precise',dict(document_ids=[docs[0]],revision='1',pages=[2]),[page2['id']],[])
    rev2=[c['id'] for c in claims if c['document_id']==docs[1]]
    run('revision-only-excludes-working',dict(revision='2'),[])
    pages1=[c['id'] for c in claims if c['locator'].startswith('page:1:')]
    # Conflicting reviewed values quarantine canon rather than granting authority.
    result=w.memory_context('local-operator',sid,'maximum temperature',**({'pages':[1]} if 'pages' in inspect.signature(w.memory_context).parameters else {}))
    alternatives=[v for g in result['hypotheses'] for values in g['alternatives'].values() for v in values]
    cases.append(dict(name='page-only-conflict-scope',pass_=bool(alternatives) and all(v['locator'].startswith('page:1:') for v in alternatives) and not result['working']))
    if 'pages' in inspect.signature(w.memory_context).parameters:
        from fastapi.testclient import TestClient
        with tempfile.TemporaryDirectory() as folder:
            token=secrets.token_hex(32);path=Path(folder)/'role.txt';path.write_text(token);os.environ['NSAI_API_TOKEN_FILE']=str(path)
            from nsai.api import app
            with TestClient(app) as client:
                response=client.post('/v1/chat',headers={'Authorization':'Bearer '+token},json=dict(question='What is the maximum operating temperature?',document_ids=[docs[0]],revision='1',pages=[1],session_id=sid))
                body=response.json();memory=body.get('memory',{})
                cases.append(dict(name='public-chat-exact-page-revision',pass_=response.status_code==200 and not body.get('conflicts') and bool(body.get('citations')) and all(c['locator'].startswith('page:1:') for c in body.get('citations',[])) and '75 C' in body.get('answer','') and '95 C' not in body.get('answer','') and {r['id'] for r in memory.get('reflection',[])}=={'target-reflection'} and not memory.get('working'),status=response.status_code,body=body))
        with store.connect() as c:c.execute("UPDATE claims SET status='rejected' WHERE id=%s",(target['id'],))
        historical=w.scoped_claims(document_ids=[docs[0]],pages=[1]);active=w.scoped_claims(document_ids=[docs[0]],pages=[1],active_only=True)
        cases.append(dict(name='historical-label-preserved-active-excluded',pass_=len(historical)==1 and historical[0]['status']=='rejected' and not active))
        rejected=w.memory_context('local-operator',sid,document_ids=[docs[0]],pages=[1])
        cases.append(dict(name='rejected-source-reflection-excluded',pass_=not rejected['canon'] and not rejected['reflection']))
        with store.connect() as c:
            c.execute("UPDATE claims SET status='verified' WHERE id=%s",(target['id'],))
            c.execute("INSERT INTO claims(id,document_id,subject,predicate,value,locator) SELECT 'legacy-'||i,%s,'synthetic capacity fixture','operating limit','1C','page:2:line:'||i FROM generate_series(1,2001) i",(docs[1],))
        scoped=w.memory_context('local-operator',sid,document_ids=[docs[0]],revision='1',pages=[1])
        failed_closed=False
        try:w.scoped_claims()
        except RuntimeError:failed_closed=True
        cases.append(dict(name='scope-before-capacity-and-global-fail-closed',pass_={c['id'] for c in scoped['canon']}=={target['id']} and failed_closed))
    print(json.dumps(dict(cases=cases,all_pass=all(c['pass_'] for c in cases),documents=2,original_fixture=True,no_models=True)))
    return 0 if all(c['pass_'] for c in cases) else 1

if __name__=='__main__':raise SystemExit(main())
