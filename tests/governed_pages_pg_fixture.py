"""Owned PG: complete immutable candidate pages, retained rationale and private dependency audit."""
import json,os
from pathlib import Path
from nsai import store,governed_store as governed,governed_pages as pages
from nsai.contracts.evidence import canonical_hash
from semantic_fixture_helpers import configure_authority,publish_pending
secret=Path('/tmp/governed-db-password');secret.write_text('x'*48,encoding='utf-8')
os.environ.update(NSAI_DB_HOST='127.0.0.1',NSAI_DB_NAME='nsai',NSAI_DB_USER='nsai_app',NSAI_DB_PASSWORD_FILE=str(secret))
configure_authority()
operator=dict(actor='local-operator',role='operator',permissions=['read','propose'])
reviewer=dict(actor='local-reviewer',role='reviewer',permissions=['read','review'])
def who(name):return dict(actor='local-user-'+name,role='admin' if name=='admin' else 'operator',identity_kind='local-user',permissions=['read','review','admin'] if name=='admin' else ['read','propose','ingest'])
with store.identity_context(operator):
 source=store.store_document('Governed page source','Motor-X maximum operating temperature is 75 C.','1',operator['actor'])['document_id']
publish_pending()
with store.identity_context(operator):
 digest=governed.w.source(source)['original_sha256']
 with store.connect() as conn:
  for number in range(165):
   payload=dict(note='Synthetic retained governed record '+str(number))
   identifier=canonical_hash(dict(kind='proposal',author=operator['actor'],document_id=source,source_sha256=digest,payload=payload))
   conn.execute('INSERT INTO governed_records(id,kind,author,document_id,source_sha256,payload,source_ids,provenance_complete) VALUES(%s,%s,%s,%s,%s,%s::jsonb,%s,true)',(identifier,'proposal',operator['actor'],source,digest,json.dumps(payload),[source]))
 first=pages.page();assert first['total']==165 and first['has_more'];cursor=first['next_cursor']
 collected=[];position=None
 while True:
  result=pages.page(cursor=position);collected.extend(row['id'] for row in result['items'])
  assert all(row['author']==operator['actor'] and row['source_ids']==[source] and row['provenance_complete'] is True for row in result['items'])
  if not result['has_more']:break
  position=result['next_cursor']
 assert len(collected)==len(set(collected))==165
 assert [row['id'] for row in pages.page(limit=5,offset=25)['items']]==collected[25:30]
 assert pages.page(kind='issues')['total']==0
 for options in [dict(cursor=cursor,kind='issues'),dict(cursor=cursor,state='candidate')]:
  try:pages.page(**options)
  except ValueError:pass
  else:raise AssertionError('Changed-filter cursor accepted')
 target=collected[0]
 assert governed.record(operator['actor'],target)['can_review'] is False
 try:governed.review(operator['actor'],target,'reviewed','Self review must be rejected.')
 except PermissionError:pass
 else:raise AssertionError('Self review accepted')
with store.identity_context(reviewer):
 assert pages.page(limit=100)['total']==165
 try:pages.page(cursor=cursor)
 except ValueError:pass
 else:raise AssertionError('Cross-role cursor accepted')
 detail=governed.record(reviewer['actor'],target,reviewer=True)
 assert detail['can_review'] is True and detail['source_integrity_matches'] is True and detail['review'] is None and detail['source']['id']==source
 rationale='  Independent synthetic candidate review; no execution or factual authority.  '
 result=governed.review(reviewer['actor'],target,'reviewed',rationale)
 assert result['record_id']==target and result['authority_granted'] is False
 after=governed.record(reviewer['actor'],target,reviewer=True)
 assert after['can_review'] is False and after['review']['rationale']==rationale and after['review']['actor']==reviewer['actor']
 assert isinstance(after['review']['id'],str) and int(after['review']['id'])>2**53
 assert pages.page(state='reviewed')['total']==1 and pages.page(state='candidate')['total']==164
 try:governed.review(reviewer['actor'],target,'rejected','A closed review cannot be overwritten.')
 except ValueError:pass
 else:raise AssertionError('Closed review overwritten')
with store.identity_context(who('bob')):
 originals=[store.store_document('Private governed '+name,'Motor-'+name+' maximum operating temperature is '+str(value)+' C.','1','local-user-bob')['document_id'] for name,value in [('A',55),('B',65)]]
publish_pending()
with store.identity_context(who('bob')):
 with store.connect() as conn:
  for document in originals:
   conn.execute("SELECT nsai_current_source_share(%s,1,'user','local-user-alice',NULL,false)",(document,))
   conn.execute("SELECT nsai_current_source_share(%s,2,'user','local-user-admin',NULL,false)",(document,))
with store.identity_context(who('alice')):
 assert pages.page()['total']==0
 made=governed.persist('proposal','local-user-alice',originals[0],dict(note='Two-source private candidate',source_ids=originals))
 assert pages.page()['total']==1
with store.identity_context(who('admin')):
 private=governed.record('local-user-admin',made['id'],reviewer=True);assert private['can_review'] is True
 result=governed.review('local-user-admin',made['id'],'reviewed','  Source-bound private rationale retained verbatim.  ')
 retained=governed.record('local-user-admin',made['id'],reviewer=True)
 with store.connect() as conn:
  audit=conn.execute('SELECT details,source_ids FROM audit_events WHERE sha256=%s',(result['audit_receipt'],)).fetchone()
  assert sorted(audit[1])==sorted(originals) and sorted(audit[0]['source_ids'])==sorted(originals)
with store.identity_context(who('bob')):
 with store.connect() as conn:conn.execute("SELECT nsai_current_source_share(%s,3,'user','local-user-admin',NULL,true)",(originals[1],))
with store.identity_context(who('admin')):
 assert governed.w.original_source(originals[0])[0]
 assert not any(row['id']==made['id'] for row in pages.page(limit=100)['items'])
 try:governed.record('local-user-admin',made['id'],reviewer=True)
 except LookupError:pass
 else:raise AssertionError('Revoked comparison record leaked')
 with store.connect() as conn:assert conn.execute('SELECT details FROM audit_events WHERE sha256=%s',(result['audit_receipt'],)).fetchone() is None
with store.identity_context(who('bob')):
 with store.connect() as conn:conn.execute("SELECT nsai_current_source_share(%s,4,'user','local-user-admin',NULL,false)",(originals[1],))
with store.identity_context(who('admin')):
 restored=governed.record('local-user-admin',made['id'],reviewer=True)
 assert restored['payload']==retained['payload'] and restored['review']==retained['review']
 with store.connect() as conn:assert conn.execute('SELECT details,source_ids FROM audit_events WHERE sha256=%s',(result['audit_receipt'],)).fetchone()==audit
# Actual HTTP contract and unchanged fail-closed individual admission.
from fastapi.testclient import TestClient
from nsai import api
for role,variable in [('operator','NSAI_API_TOKEN_FILE'),('reviewer','NSAI_REVIEWER_TOKEN_FILE')]:
 path=Path('/tmp/governed-'+role);path.write_text(('synthetic-governed-'+role).ljust(48,'x'),encoding='utf-8');os.environ[variable]=str(path)
auth=lambda role:{'Authorization':'Bearer '+Path('/tmp/governed-'+role).read_text(encoding='utf-8')}
with TestClient(api.app) as client:
 assert client.get('/v1/governed/records').status_code==401
 response=client.get('/v1/governed/records?state=reviewed',headers=auth('reviewer'));assert response.status_code==200 and response.json()['total']==1
 assert client.get('/v1/governed/records?state=applied',headers=auth('reviewer')).status_code==422
 assert client.get('/v1/governed/records/'+target,headers=auth('reviewer')).json()['review']['rationale']==rationale
 assert client.post('/v1/governed/records/'+target+'/review',headers=auth('operator'),json=dict(decision='reviewed',rationale='An operator cannot independently review.')).status_code==403
 assert client.get('/v1/governed/records',headers={'Authorization':'Bearer '+Path('/tmp/fixture-user-alice').read_text()}).status_code==503
print(json.dumps(dict(status='PASS_SCOPED',all_165_reachable=True,legacy_offset_order_preserved=True,exact_review_history=True,multi_source_audit_revocation_without_deletion=True,individual_http_closed=True)))
