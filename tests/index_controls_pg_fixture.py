"""Actual packaged owner controls and atomic audit rollback; private HTTP stays blocked."""
import hashlib,json,sys,os
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,'/')
from semantic_fixture_helpers import configure_authority
from nsai import api,security,store,workflow_store as workflow,semantic_jobs as jobs
from nsai.ingestion import parse_source
from fastapi.testclient import TestClient
secret=Path('/tmp/index-control-db-password');secret.write_text('x'*48,encoding='utf-8')
os.environ.update(NSAI_DB_HOST='127.0.0.1',NSAI_DB_NAME='nsai',NSAI_DB_USER='nsai_app',NSAI_DB_PASSWORD_FILE=str(secret))
configure_authority()
def identity(name):return security.resolve_principal('Bearer '+Path('/tmp/fixture-user-'+name).read_text())
checks=[]
def check(name,value):
 if not value:raise AssertionError(name)
 checks.append(name)
def audit_count():
 with store.connect() as conn:return conn.execute("SELECT count(*) FROM audit_events WHERE event_type LIKE 'index.%'").fetchone()[0]
original=b'Exact retained original for index control audit rollback.'
with store.identity_context(identity('alice')):
 saved=workflow.persist_source('Audited queue source','1',original,parse_source(original,'queue.txt'),'local-user-alice');doc=saved['document_id'];before=jobs.source_status(doc)
 for action in [lambda:jobs.set_priority(doc,before['epoch'],7),lambda:jobs.cancel(doc,before['epoch'])]:
  try:
   with patch('nsai.workflow_store.audit',side_effect=RuntimeError('Owned audit commit failure')):action()
  except RuntimeError:pass
  else:raise AssertionError('Owned audit failure was not propagated')
  after=jobs.source_status(doc)
  check('failed audit rolls back queue epoch state and priority',after['epoch']==before['epoch'] and after['job_state']=='queued' and after['priority']==0 and audit_count()==0)
 changed=jobs.set_priority(doc,before['epoch'],7)
 check('owner priority returns exact source job epoch and audit proof',changed['document_id']==doc and changed['job_id']==before['job_id'] and changed['priority']==7 and changed['epoch']==before['epoch']+1 and len(changed['audit_receipt'])==64)
 with store.connect() as conn:
  audit=conn.execute("SELECT sha256,source_ids,provenance_complete,details FROM audit_events WHERE event_type='index.priority-changed'").fetchone()
 check('actual priority audit has complete source binding and exact requested epoch',audit[0]==changed['audit_receipt'] and audit[1]==[doc] and audit[2] is True and audit[3]['expected_epoch']==before['epoch'])
 cancelled=jobs.cancel(doc,changed['epoch']);status=jobs.source_status(doc)
 check('owner cancellation confirms invalidated pending job with audit',cancelled['job_id']==before['job_id'] and cancelled['state']=='cancelled' and status['job_state']=='cancelled' and audit_count()==2)
 try:jobs.cancel(doc,changed['epoch'])
 except Exception as error:check('duplicate cancellation is stale without extra audit',getattr(error,'sqlstate',None)=='40001' and audit_count()==2)
 else:raise AssertionError('Duplicate cancellation succeeded')
 queued=jobs.retry(doc,status['epoch']);status=jobs.source_status(doc)
 check('cancelled job resumes explicitly with same identity and separate audit',queued==dict(job_id=before['job_id'],state='queued') and status['job_state']=='queued' and audit_count()==3)
 check('original bytes and hash survive all committed and rolled-back controls',workflow.original_source(doc)[0]==original and hashlib.sha256(original).hexdigest()==saved['sha256'])
 with store.connect() as conn:conn.execute("SELECT nsai_current_source_share(%s,1,'user','local-user-bob',NULL,false)",(doc,))
for name in ['bob','admin']:
 with store.identity_context(identity(name)):
  for function in [lambda:jobs.set_priority(doc,status['epoch'],9),lambda:jobs.cancel(doc,status['epoch']),lambda:jobs.retry(doc,status['epoch'])]:
   try:function()
   except LookupError:checks.append('shared reader or admin cannot mutate another owner queue')
   else:raise AssertionError('Foreign identity controlled owner queue')
with TestClient(api.app) as client:
 headers={'Authorization':'Bearer '+Path('/tmp/fixture-user-alice').read_text()}
 for route,body in [('index-priority',dict(expected_epoch=status['epoch'],priority=9)),('cancel-index',dict(expected_epoch=status['epoch'])),('retry-index',dict(expected_epoch=status['epoch']))]:
  check('actual private HTTP control remains503',client.post('/v1/sources/'+doc+'/'+route,headers=headers,json=body).status_code==503)
print(json.dumps(dict(status='PASS_SCOPED',checks=checks,private_http_admitted=False,source_original_sha256=hashlib.sha256(original).hexdigest())))
