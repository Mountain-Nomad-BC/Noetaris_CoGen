"""Owned exact-query EXPLAIN diagnostic; its longer SQL deadline is never production policy."""
from contextlib import contextmanager
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4
from psycopg import sql as pg_sql

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'scripts'))
from check_release_readiness import source_snapshot
from nsai import store,workflow_store
from test_private_access_database import database
from test_claim_context_database import test_duplicates_and_unrelated_corpus_do_not_hide_a_conflicting_witness


class Captured(Exception):pass


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate-indexes',action='store_true')
    args=parser.parse_args()
    owner=uuid4().hex;folder=ROOT/'evidence/claim-context-plan'/owner;folder.mkdir(parents=True)
    report=dict(status='FAIL',scope=__doc__,source_before=source_snapshot(ROOT),
        producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        live_services_accessed=False,release_approved=False,diagnostic_statement_timeout_seconds=60)
    captured={};seed=[];generator=None
    class Connection:
        def execute(self,query,arguments):captured.update(query=query,arguments=arguments);raise Captured()
    @contextmanager
    def connection():yield Connection()
    original=store.connect
    try:
        store.connect=connection
        try:workflow_store.claim_context([dict(document_id='legacy',locator='line:1',source_segments=[dict(locator='line:2')])])
        except Captured:pass
    finally:store.connect=original
    def seed_capture(body):seed.append(body)
    def stopped(*args):raise Captured()
    seed_capture.run_source_fixture=stopped
    try:test_duplicates_and_unrelated_corpus_do_not_hide_a_conflicting_witness(seed_capture)
    except Captured:pass
    assert len(seed)==1 and captured['query'].count('%s')==len(captured['arguments'])
    parts=captured['query'].split('%s')
    query=''.join(part+pg_sql.Literal(value).as_string() for part,value in zip(parts,captured['arguments']))+parts[-1]
    (folder/'query.sql').write_text(query,encoding='utf-8');(folder/'seed.sql').write_text(seed[0],encoding='utf-8')
    try:
        image=subprocess.run(['docker','image','inspect','postgres:16-alpine','--format','{{.Id}}'],capture_output=True,check=True,timeout=30).stdout.decode().strip()
        os.environ.update(NSAI_TEST_PRIVATE_DATABASE='1',NSAI_TEST_PRIVATE_DATABASE_IMAGE=image,NSAI_TEST_PRIVATE_OWNER=owner)
        report['database_image']=image
        generator=database.__wrapped__();sql=next(generator);sql(seed[0])
        if args.candidate_indexes:
            indexes="""CREATE INDEX diagnostic_claim_source_span ON claims(document_id,locator,subject,predicate,value,status,id)
                WHERE status NOT IN ('superseded','rejected');
                CREATE INDEX diagnostic_claim_alternative ON claims(subject,predicate,value,(status='verified') DESC,id)
                WHERE status NOT IN ('superseded','rejected');"""
            (folder/'experimental-indexes.sql').write_text(indexes,encoding='utf-8');sql(indexes)
        report['experimental_indexes']=args.candidate_indexes
        static=sql('EXPLAIN (VERBOSE,FORMAT JSON) '+query,app=True)
        (folder/'estimated-plan.json').write_text(static+'\n',encoding='utf-8')
        raw=sql("SET statement_timeout='60s'; EXPLAIN (ANALYZE,BUFFERS,VERBOSE,FORMAT JSON) "+query,app=True)
        (folder/'plan.json').write_text(raw+'\n',encoding='utf-8')
        plan=json.loads(raw)[0]
        report.update(status='PLAN_CAPTURED_ONLY',planning_ms=plan['Planning Time'],execution_ms=plan['Execution Time'])
    except Exception as error:report.update(failure_type=type(error).__name__,failure=str(error)[-1500:])
    finally:
        if generator is not None:generator.close()
        remaining=subprocess.run(['docker','ps','-aq','--filter','label=nsai.owner='+owner],capture_output=True,timeout=30)
        report['cleanup_complete']=remaining.returncode==0 and not remaining.stdout.strip()
        report['source_after']=source_snapshot(ROOT)
        if report['source_before']!=report['source_after'] or not report['cleanup_complete']:report['status']='FAIL'
        report['artifact_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.iterdir() if p.is_file()}
        (folder/'receipt.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report.get(k) for k in ('status','execution_ms','failure','cleanup_complete')}))
    print(str(folder))
    return 0 if report['status']=='PLAN_CAPTURED_ONLY' else 1


if __name__=='__main__':raise SystemExit(main())
