"""Real PostgreSQL proposal pagination, actor scopes and revocation; no model quality claim."""
import json,os
from pathlib import Path
from nsai import store,workflow_store as workflows,learning_pages as pages
from semantic_fixture_helpers import configure_authority,publish_pending
secret=Path('/tmp/learning-db-password');secret.write_text('x'*48,encoding='utf-8')
os.environ.update(NSAI_DB_HOST='127.0.0.1',NSAI_DB_NAME='nsai',NSAI_DB_USER='nsai_app',NSAI_DB_PASSWORD_FILE=str(secret))
configure_authority()
operator=dict(actor='local-operator',role='operator',permissions=['read','propose'])
reviewer=dict(actor='local-reviewer',role='reviewer',permissions=['read','review'])
def who(name):return dict(actor='local-user-'+name,role='operator',identity_kind='local-user',permissions=['read','propose','ingest'])
with store.identity_context(operator):
 document=store.store_document('Pagination fixture','Motor-X maximum operating temperature is 75 C.','1',operator['actor'])['document_id']
publish_pending()
with store.identity_context(operator):
 claim=next(row for row in store.all_claims() if row['document_id']==document)
 with store.connect() as conn:
  for number in range(165):
   conn.execute("INSERT INTO learning_proposals(id,author,source_claim_id,reflection,state,source_ids,provenance_complete) VALUES(%s,%s,%s,%s,'reviewed',%s,true)",(f'{number:032x}',operator['actor'],claim['id'],'Synthetic retained proposal '+str(number),[document]))
 own=pages.page(own=True);assert own['total']==165 and own['has_more'];cursor=own['next_cursor']
 collected=[];position=None
 while True:
  result=pages.page(own=True,cursor=position);collected.extend(row['id'] for row in result['items'])
  assert all(row['author']==operator['actor'] and row['source_claim']['document_id']==document for row in result['items'])
  if not result['has_more']:break
  position=result['next_cursor']
 assert len(collected)==len(set(collected))==165
 try:pages.page(own=True,cursor=cursor,state='candidate')
 except ValueError:pass
 else:raise AssertionError('Changed filter cursor accepted')
 assert pages.page(own=True,state='candidate')['total']==0
with store.identity_context(reviewer):
 assert pages.page(limit=100)['total']==165
 try:pages.page(cursor=cursor)
 except ValueError:pass
 else:raise AssertionError('Cross-role/view cursor accepted')
with store.identity_context(who('alice')):
 assert pages.page(own=True)['total']==0
 try:pages.page(own=True,cursor=cursor)
 except ValueError:pass
 else:raise AssertionError('Cross-author cursor accepted')
with store.identity_context(who('bob')):
 private=store.store_document('Private proposal source','Motor-Y maximum operating temperature is 85 C.','1','local-user-bob')['document_id']
publish_pending()
with store.identity_context(who('bob')):
 private_claim=next(row for row in store.all_claims() if row['document_id']==private)
 with store.connect() as conn:conn.execute("SELECT nsai_current_source_share(%s,1,'user','local-user-alice',NULL,false)",(private,))
with store.identity_context(who('alice')):
 with store.connect() as conn:
  diagnostic=conn.execute('SELECT nsai_actor(),nsai_sources_visible(%s,true),source_ids,provenance_complete,document_id FROM claims WHERE id=%s',([private],private_claim['id'])).fetchone()
  assert diagnostic[0]=='local-user-alice' and diagnostic[1] is True and diagnostic[2]==[] and diagnostic[3] is False
 made=workflows.propose_learning('local-user-alice',private_claim['id'],'Private retained reflection requiring attributable review.')
 visible=pages.page(own=True);assert visible['total']==1 and visible['items'][0]['id']==made['id']
 for author,sources,complete in [('local-user-alice',[],True),('local-user-alice',[private],False),('local-user-bob',[private],True)]:
  try:
   with store.connect() as conn:conn.execute("INSERT INTO learning_proposals(id,author,source_claim_id,reflection,source_ids,provenance_complete) VALUES(%s,%s,%s,%s,%s,%s)",('f'*32,author,private_claim['id'],'Forged proposal must not be admitted.',sources,complete))
  except Exception as error:
   assert getattr(error,'sqlstate',None)=='42501'
  else:raise AssertionError('Invalid proposal provenance admitted')
with store.identity_context(who('bob')):
 with store.connect() as conn:conn.execute("SELECT nsai_current_source_share(%s,2,'user','local-user-alice',NULL,true)",(private,))
with store.identity_context(who('alice')):assert pages.page(own=True)['items']==[]
with store.identity_context(who('bob')):
 with store.connect() as conn:
  conn.execute("SELECT nsai_current_source_share(%s,3,'user','local-user-alice',NULL,false)",(private,))
with store.identity_context(who('alice')):
 restored=pages.page(own=True)['items'][0]
 assert restored['id']==made['id'] and restored['reflection']=='Private retained reflection requiring attributable review.'
# Real HTTP role checks, preserving the closed individual content gate.
from fastapi.testclient import TestClient
from nsai import api
for role,variable in [('operator','NSAI_API_TOKEN_FILE'),('reviewer','NSAI_REVIEWER_TOKEN_FILE')]:
 token=Path('/tmp/learning-'+role);token.write_text(('synthetic-'+role).ljust(48,'x'),encoding='utf-8');os.environ[variable]=str(token)
with TestClient(api.app) as client:
 assert client.get('/v1/learning/own').status_code==401
 auth=lambda role:{'Authorization':'Bearer '+Path('/tmp/learning-'+role).read_text(encoding='utf-8')}
 assert client.get('/v1/learning/own',headers=auth('operator')).json()['total']==165
 assert client.get('/v1/learning',headers=auth('operator')).status_code==403
 assert client.get('/v1/learning',headers=auth('reviewer')).json()['has_more'] is True
 assert client.get('/v1/learning/own',headers={'Authorization':'Bearer '+Path('/tmp/fixture-user-alice').read_text()}).status_code==503
with store.identity_context(operator):
 created=workflows.propose_learning(operator['actor'],claim['id'],'Audited reflection remains noncanonical after review.')
 try:workflows.review_learning(operator['actor'],created['id'],1,True,'Self-review must be rejected.')
 except PermissionError:pass
 else:raise AssertionError('Self review accepted')
with store.identity_context(reviewer):
 try:workflows.review_learning(reviewer['actor'],created['id'],999,True,'Stale decision must not commit.')
 except ValueError:pass
 else:raise AssertionError('Stale revision accepted')
 rationale='Independent synthetic policy review; not factual acceptance.'
 result=workflows.review_learning(reviewer['actor'],created['id'],1,True,rationale)
 assert result['id']==created['id'] and result['state']=='reviewed' and result['revision']==2 and result['authority_granted'] is False
 with store.connect() as conn:
  details=conn.execute("SELECT details FROM audit_events WHERE sha256=%s",(result['audit_receipt'],)).fetchone()[0]
  assert details['rationale']==rationale and details['previous_revision']==1 and details['revision']==2 and details['source_claim_id']==claim['id']
 try:workflows.review_learning(reviewer['actor'],created['id'],1,False,'A repeat decision cannot overwrite review.')
 except ValueError:pass
 else:raise AssertionError('Closed/repeated decision accepted')
print(json.dumps(dict(status='PASS_SCOPED' ,all_165_retained_records_reachable=True,actor_filter_and_cursor_bound=True,revocation_withholds_without_deletion=True,candidate_claim_proposal_and_forged_source_negatives=True,actual_http_roles_and_closed_individual_gate=True)))
