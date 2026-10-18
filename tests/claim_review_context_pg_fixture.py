"""Actual claim context, phantom-insert review scope, exact events and revocation."""
import json,os
from pathlib import Path
from unittest.mock import patch
from nsai import store,workflow_store as w,claim_review as inspection,source_dependencies
from semantic_fixture_helpers import configure_authority,publish_pending
secret=Path('/tmp/claim-review-db-password');secret.write_text('x'*48,encoding='utf-8')
os.environ.update(NSAI_DB_HOST='127.0.0.1',NSAI_DB_NAME='nsai',NSAI_DB_USER='nsai_app',NSAI_DB_PASSWORD_FILE=str(secret))
configure_authority()
operator=dict(actor='local-operator',role='operator',permissions=['read','ingest'])
reviewer=dict(actor='local-reviewer',role='reviewer',permissions=['read','review'])
viewer=dict(actor='local-viewer',role='viewer',permissions=['read'])
def who(name,role='operator'):return dict(actor='local-user-'+name,role=role,identity_kind='local-user',permissions=['read','review'] if role=='admin' else ['read','ingest'])
def ingest(value):
 with store.identity_context(operator):
  document=store.store_document('Context source '+str(value),'Motor-X maximum operating temperature is '+str(value)+' C.','1',operator['actor'])['document_id']
  with store.connect() as conn:claim=conn.execute('SELECT id FROM claims WHERE document_id=%s',(document,)).fetchone()[0]
 return document,claim
one,target=ingest(75);two,other=ingest(85);publish_pending()
with store.identity_context(reviewer):
 first=inspection.detail(target)
 assert first['total_alternatives']==1 and first['alternatives'][0]['id']==other and first['can_review'] is True
 assert first['citation']['document_id']==one and '75' in first['citation']['excerpt'] and first['citation']['original_sha256']==first['claim']['original_sha256']
 first_hash=first['context_sha256']
with store.identity_context(viewer):
 visible=inspection.detail(target);assert visible['can_review'] is False and visible['context_sha256']!=first_hash
three,third=ingest(95);publish_pending()
with store.identity_context(reviewer):
 try:w.review(target,'accept',1,'Stale comparison must not apply.',reviewer['actor'],expected_context=first_hash)
 except ValueError as error:assert 'context changed' in str(error)
 else:raise AssertionError('Unseen comparison accepted')
 fresh=inspection.detail(target);assert fresh['total_alternatives']==2
 original_collect=source_dependencies.collect_sources;injected=[]
 def insert_between_snapshot_and_update(*values,**kwargs):
  if not injected:
   injected.append(True);injected.append(ingest(105)[1])
  return original_collect(*values,**kwargs)
 # No fake positive response: persist a real new source between the locked
 # comparison read and mutation, using the actual source ingestion transaction.
 with patch.object(source_dependencies,'collect_sources',side_effect=insert_between_snapshot_and_update):
  accepted=w.review(target,'accept',1,'Inspected original source and both locked alternatives.',reviewer['actor'],expected_context=fresh['context_sha256'])
 assert accepted['claim_id']==target and accepted['revision']==2 and accepted['superseded_count']==2
 with store.connect() as conn:
  observed=dict(conn.execute('SELECT id,status FROM claims WHERE id=ANY(%s)',([target,other,third,injected[1]],)).fetchall())
  assert observed=={target:'verified',other:'superseded',third:'superseded',injected[1]:'candidate'}
  audit=conn.execute('SELECT details FROM audit_events WHERE sha256=%s',(accepted['audit_receipt'],)).fetchone()[0]
  assert audit['review_context_sha256']==fresh['context_sha256'] and len(audit['alternatives_superseded'])==2
 # Produce real history beyond one event page; IDs are configured above2^53.
 for _ in range(27):
  current=inspection.detail(target)
  w.review(target,'contest',current['claim']['revision'],'Retained synthetic contested review event.',reviewer['actor'],expected_context=current['context_sha256'])
 result=inspection.events(target);first_event=result['items'][0]['id']
 assert isinstance(first_event,str) and int(first_event)>9007199254740992 and result['has_more']
 ids=[];position=None
 while True:
  result=inspection.events(target,before_id=position);ids.extend(row['id'] for row in result['items'])
  if not result['has_more']:break
  position=result['next_before_id']
 assert len(ids)==len(set(ids))==29 and all(isinstance(identity,str) for identity in ids)
with store.identity_context(who('bob')):
 private=store.store_document('Private claim context','Motor-Z maximum operating temperature is 65 C.','1','local-user-bob')['document_id']
 with store.connect() as conn:private_claim=conn.execute('SELECT id FROM claims WHERE document_id=%s',(private,)).fetchone()[0]
with store.identity_context(who('admin','admin')):
 try:inspection.detail(private_claim)
 except LookupError:pass
 else:raise AssertionError('Admin bypassed private source authorization')
with store.identity_context(who('bob')):
 with store.connect() as conn:conn.execute("SELECT nsai_current_source_share(%s,1,'user','local-user-admin',NULL,false)",(private,))
with store.identity_context(who('admin','admin')):
 private_context=inspection.detail(private_claim);assert private_context['claim']['document_id']==private and private_context['can_review'] is True
with store.identity_context(who('bob')):
 with store.connect() as conn:conn.execute("SELECT nsai_current_source_share(%s,2,'user','local-user-admin',NULL,true)",(private,))
with store.identity_context(who('admin','admin')):
 for read in [lambda:inspection.detail(private_claim),lambda:inspection.events(private_claim)]:
  try:read()
  except LookupError:pass
  else:raise AssertionError('Revoked claim context leaked')
with store.identity_context(who('bob')):
 with store.connect() as conn:conn.execute("SELECT nsai_current_source_share(%s,3,'user','local-user-admin',NULL,false)",(private,))
with store.identity_context(who('admin','admin')):assert inspection.detail(private_claim)['context_sha256']==private_context['context_sha256']
with store.identity_context(who('alice')):
 alternative_document=store.store_document('Private comparison alternative','Motor-Z maximum operating temperature is 75 C.','1','local-user-alice')['document_id']
 with store.connect() as conn:conn.execute("SELECT nsai_current_source_share(%s,1,'user','local-user-admin',NULL,false)",(alternative_document,))
with store.identity_context(who('admin','admin')):
 compared=inspection.detail(private_claim);assert compared['total_alternatives']==1
 w.review(private_claim,'contest',1,'Both authorized private source alternatives were inspected.','local-user-admin',expected_context=compared['context_sha256'])
 derived=inspection.detail(private_claim)
 assert set(derived['claim']['source_ids'])=={private,alternative_document}
with store.identity_context(who('alice')):
 with store.connect() as conn:conn.execute("SELECT nsai_current_source_share(%s,2,'user','local-user-admin',NULL,true)",(alternative_document,))
with store.identity_context(who('admin','admin')):
 # Primary custody remains readable, but the comparison-derived claim/events
 # must be withheld after loss of the other source used in its context hash.
 assert b'65' in w.original_source(private)[0]
 for read in [lambda:inspection.detail(private_claim),lambda:inspection.events(private_claim)]:
  try:read()
  except LookupError:pass
  else:raise AssertionError('Comparison-derived review omitted a revoked alternative dependency')
with store.identity_context(who('alice')):
 with store.connect() as conn:conn.execute("SELECT nsai_current_source_share(%s,3,'user','local-user-admin',NULL,false)",(alternative_document,))
with store.identity_context(who('admin','admin')):assert inspection.detail(private_claim)['context_sha256']==derived['context_sha256']
from fastapi.testclient import TestClient
from nsai import api
credential=Path('/tmp/context-reviewer');credential.write_text('synthetic-reviewer-proof'.ljust(48,'x'),encoding='utf-8');os.environ['NSAI_REVIEWER_TOKEN_FILE']=str(credential)
with TestClient(api.app) as client:
 headers={'Authorization':'Bearer '+credential.read_text()}
 assert client.get('/v1/claims/'+target).status_code==401
 assert client.get('/v1/claims/'+target,headers=headers).status_code==200
 assert client.get('/v1/claims/'+target+'/events',headers=headers).json()['has_more'] is True
 assert client.get('/v1/claims/'+target+'/events',params={'before_id':first_event},headers=headers).status_code==200
 assert client.get('/v1/claims/'+target+'/events',params={'before_id':'9223372036854775808'},headers=headers).status_code==409
 assert client.get('/v1/claims/'+private_claim,headers={'Authorization':'Bearer '+Path('/tmp/fixture-user-admin').read_text()}).status_code==503
print(json.dumps(dict(status='PASS_SCOPED',context_binds_actor_and_full_visible_group=True,stale_context_rejected=True,new_concurrent_candidate_not_superseded=True,all_29_exact_event_ids_reachable=True,explicit_private_grant_and_revoke=True,nonaccepting_review_retains_full_comparison_dependencies=True,actual_http_roles_and_individual_gate=True)))
