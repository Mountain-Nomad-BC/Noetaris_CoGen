"""Real SQL acceptance cases for owner queue controls; vector quality is outside scope."""
import json,os
from pathlib import Path
import pytest
from test_durable_semantic_jobs import prepare,claim
from test_private_access_database import database
pytestmark=pytest.mark.skipif(os.getenv('NSAI_TEST_PRIVATE_DATABASE')!='1',reason='explicit owned PostgreSQL qualification')
def epoch(database,doc):return int(database(f"SELECT epoch FROM source_index_state WHERE document_id='{doc}';"))
def test_cancel_retains_job_and_queued_source_and_rejects_stale_or_foreign_actor(database):
 job,_=prepare(database)
 version=epoch(database,'job-source')
 database(f"SELECT nsai_cancel_semantic_job('job-source',{version});",app=True,actor='local-user-bob',ok=False)
 cancelled=json.loads(database(f"SELECT nsai_cancel_semantic_job('job-source',{version});",app=True,actor='local-user-alice'))
 assert cancelled['job_id']==job and cancelled['state']=='cancelled' and cancelled['epoch']==version+1
 assert database(f"SELECT state FROM semantic_jobs WHERE id='{job}';")=='cancelled'
 assert database("SELECT state FROM source_index_state WHERE document_id='job-source';")=='cancelled'
 assert database("SELECT count(*) FROM documents WHERE id='job-source';")=='1'
 assert database("SELECT count(*) FROM document_knowledge WHERE document_id='job-source';")=='1'
 database(f"SELECT nsai_cancel_semantic_job('job-source',{version});",app=True,actor='local-user-alice',ok=False)
 assert database("SELECT count(*) FROM semantic_job_events WHERE event_type='cancelled';")=='1'
 assert database(f"SELECT nsai_retry_semantic_job('job-source',{version+1});",app=True,actor='local-user-alice')==job
 assert database('SELECT count(*) FROM semantic_jobs;')=='1'
def test_cancel_running_invalidates_exact_worker_lease_without_deleting_source(database):
 job,_=prepare(database);leased=claim(database);version=epoch(database,'job-source')
 assert leased['id']==job
 database(f"SELECT nsai_cancel_semantic_job('job-source',{version});",app=True,actor='local-user-alice')
 assert database("SELECT count(*) FROM documents;",app=True,actor='local-user-alice',job=leased)=='0'
 assert database(f"SELECT (lease_token IS NULL AND lease_expires_at IS NULL)::text FROM semantic_jobs WHERE id='{job}';")=='true'
 assert database("SELECT count(*) FROM documents WHERE id='job-source';",app=True,actor='local-user-alice')=='1'
def test_priority_is_owner_bound_epoch_checked_and_orders_within_actor_fairness(database):
 first,_=prepare(database,'alice-one');second,_=prepare(database,'alice-two');bob,_=prepare(database,'bob-one','local-user-bob')
 version=epoch(database,'alice-two')
 database(f"SELECT nsai_set_semantic_job_priority('alice-two',{version},9);",app=True,actor='local-user-bob',ok=False)
 database(f"SELECT nsai_set_semantic_job_priority('alice-two',{version},10);",app=True,actor='local-user-alice',ok=False)
 changed=json.loads(database(f"SELECT nsai_set_semantic_job_priority('alice-two',{version},9);",app=True,actor='local-user-alice'))
 assert changed['priority']==9 and changed['job_id']==second and changed['epoch']==version+1
 database(f"SELECT nsai_set_semantic_job_priority('alice-two',{version},0);",app=True,actor='local-user-alice',ok=False)
 selected=claim(database);assert selected['id']==second
 next_job=claim(database);assert next_job['id']==bob
 assert claim(database) is None
 assert database('SELECT count(*) FROM semantic_jobs;')=='3'


def test_worker_cancels_pending_encoder_after_actual_owner_cancellation(database,monkeypatch):
 import asyncio
 prepare(database);leased=claim(database);version=epoch(database,'job-source');from nsai import semantic_jobs as worker
 def active(job):return database("SELECT nsai_job_source_allowed('job-source');",app=True,actor='local-user-alice',job=job)=='t'
 monkeypatch.setattr(worker,'_lease_active',active)
 async def scenario():
  started=asyncio.Event();stopped=asyncio.Event()
  async def pending_encoder(job):
   started.set()
   try:await asyncio.Event().wait()
   finally:stopped.set()
  monkeypatch.setattr(worker,'process_job',pending_encoder)
  processing=asyncio.create_task(worker._process_with_lease(leased));await started.wait()
  database(f"SELECT nsai_cancel_semantic_job('job-source',{version});",app=True,actor='local-user-alice')
  result=await asyncio.wait_for(processing,5)
  assert result==dict(state='lease-released') and stopped.is_set()
 asyncio.run(scenario())
 assert database("SELECT count(*) FROM documents WHERE id='job-source';")=='1'
 assert database('SELECT count(*) FROM semantic_publications;')=='0'

def test_worker_preserves_completed_result_when_probe_observes_released_lease(monkeypatch):
 import asyncio,threading
 from nsai import semantic_jobs as worker
 async def scenario():
  release=asyncio.Event();finished=threading.Event();loop=asyncio.get_running_loop()
  async def committed(job):
   await release.wait();finished.set();return dict(state='succeeded',publication_id='retained')
  def after_commit(job):
   loop.call_soon_threadsafe(release.set)
   assert finished.wait(2)
   return False
  monkeypatch.setattr(worker,'process_job',committed);monkeypatch.setattr(worker,'_lease_active',after_commit)
  assert await asyncio.wait_for(worker._process_with_lease({}),5)==dict(state='succeeded',publication_id='retained')
 asyncio.run(scenario())

def test_stale_cancelled_worker_cannot_report_automatic_requeue(database,monkeypatch):
 import asyncio
 prepare(database);leased=claim(database);version=epoch(database,'job-source');from nsai import semantic_jobs as worker
 database(f"SELECT nsai_cancel_semantic_job('job-source',{version});",app=True,actor='local-user-alice')
 monkeypatch.setattr(worker,'claim_next',lambda:leased)
 async def invalid(job):raise ValueError('Lease lost before saving derived bytes')
 monkeypatch.setattr(worker,'process_job',invalid)
 def fail(job,code):return database(f"SELECT nsai_fail_semantic_job('{job['id']}','{job['lease_token']}','{code}');",app=True)=='t'
 monkeypatch.setattr(worker,'fail_job',fail)
 result=asyncio.run(worker.process_one());assert result['state']=='lease-released'
 assert database(f"SELECT state FROM semantic_jobs WHERE id='{leased['id']}';")=='cancelled'


@pytest.mark.parametrize('payload',[
 dict(expected_epoch=1,priority=True),dict(expected_epoch=1,priority=10),dict(expected_epoch=1,priority=-1),
 dict(expected_epoch=1,priority='2'),dict(expected_epoch=1,priority=None),dict(expected_epoch=1,priority=1.0),
 dict(expected_epoch=True,priority=2),dict(expected_epoch=None,priority=2),dict(expected_epoch=0,priority=2),
 dict(expected_epoch=1,priority=2,actor='local-user-alice'),
])
def test_priority_request_refuses_coercion_foreign_actor_and_invalid_ranges(payload):
 from nsai.api import IndexPriority
 with pytest.raises(ValueError):IndexPriority(**payload)

@pytest.mark.parametrize('role',['viewer','reviewer','admin'])
def test_owner_without_ingest_role_cannot_mutate_queue_through_database(database,role):
 prepare(database);version=epoch(database,'job-source')
 for function in [f"nsai_cancel_semantic_job('job-source',{version})",f"nsai_set_semantic_job_priority('job-source',{version},9)",f"nsai_retry_semantic_job('job-source',{version})"]:
  database('SELECT '+function+';',app=True,actor='local-user-alice',role=role,ok=False)
 assert epoch(database,'job-source')==version

def test_null_epochs_and_background_lease_context_cannot_mutate_controls(database):
 prepare(database);version=epoch(database,'job-source')
 for function in ["nsai_cancel_semantic_job('job-source',NULL)","nsai_set_semantic_job_priority('job-source',NULL,9)","nsai_retry_semantic_job('job-source',NULL)"]:
  database('SELECT '+function+';',app=True,actor='local-user-alice',ok=False)
 assert epoch(database,'job-source')==version
 leased=claim(database);version=epoch(database,'job-source')
 for function in [f"nsai_cancel_semantic_job('job-source',{version})",f"nsai_set_semantic_job_priority('job-source',{version},9)",f"nsai_retry_semantic_job('job-source',{version})"]:
  database('SELECT '+function+';',app=True,actor='local-user-alice',job=leased,ok=False)
 assert epoch(database,'job-source')==version

def test_concurrent_cancel_and_priority_consume_epoch_only_once(database):
 from concurrent.futures import ThreadPoolExecutor
 job,_=prepare(database);version=epoch(database,'job-source')
 functions=[f"nsai_cancel_semantic_job('job-source',{version})",f"nsai_set_semantic_job_priority('job-source',{version},9)"]
 def execute(function):return database('SELECT '+function+';',app=True,actor='local-user-alice',ok=None)
 with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(execute,functions))
 assert sorted(result.returncode==0 for result in results)==[False,True]
 assert epoch(database,'job-source')==version+1
 assert database("SELECT count(*) FROM semantic_job_events WHERE event_type IN('cancelled','priority-changed');")=='1'
 assert database("SELECT control_details->>'actor' FROM semantic_job_events WHERE event_type IN('cancelled','priority-changed');")=='local-user-alice'

def test_cancelling_pending_generation_retains_prior_valid_publication(database):
 job,digest=prepare(database);old='d'*64
 database(f"INSERT INTO semantic_jobs(id,document_id,requested_actor,source_revision,source_sha256,knowledge_sha256,model_sha256,state,attempts) VALUES('{old}','job-source','local-user-alice','1','{digest}',repeat('b',64),repeat('e',64),'succeeded',1); "
          f"INSERT INTO semantic_publications(id,document_id,model_sha256,knowledge_sha256,embedding_sha256,source_ids) VALUES('{old}','job-source',repeat('e',64),repeat('b',64),repeat('c',64),ARRAY['job-source']); "
          f"UPDATE source_index_state SET current_publication_id='{old}' WHERE document_id='job-source';")
 version=epoch(database,'job-source')
 cancelled=json.loads(database(f"SELECT nsai_cancel_semantic_job('job-source',{version});",app=True,actor='local-user-alice'))
 assert cancelled['index_state']=='ready'
 status=json.loads(database("SELECT nsai_source_index_status('job-source');",app=True,actor='local-user-alice'))
 assert status['ready'] and status['job_state']=='cancelled' and status['publication_id']==old
 assert database('SELECT count(*) FROM semantic_publications;')=='1'
 assert database(f"SELECT nsai_retry_semantic_job('job-source',{version+1});",app=True,actor='local-user-alice')==job
 assert json.loads(database("SELECT nsai_source_index_status('job-source');",app=True,actor='local-user-alice'))['ready'] is True


def test_index_control_audits_commit_or_roll_back_with_queue_state(database):
 result=database.run_source_fixture('index_controls_pg_fixture.py')
 assert result.returncode==0,result.stderr
 value=json.loads(result.stdout.strip().splitlines()[-1]);assert value['status']=='PASS_SCOPED' and value['private_http_admitted'] is False
 assert len(value['checks'])==17
