"""Owned real-PostgreSQL qualification; no host ports, volumes or live secrets.

Run explicitly with NSAI_TEST_PRIVATE_DATABASE=1. Application admission remains
closed: these tests qualify policy persistence, not the full content adapter.
"""
import importlib.util
import os
from pathlib import Path
import subprocess
import time
from uuid import uuid4

import pytest

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(os.getenv('NSAI_TEST_PRIVATE_DATABASE') != '1',
                              reason='explicit owned PostgreSQL qualification')


@pytest.fixture
def database():
    name = 'nsai-private-policy-test-' + uuid4().hex
    def docker(*args, input=None):
        result=subprocess.run(['docker', *args], input=input.encode('utf-8') if isinstance(input,str) else input,
                              capture_output=True, timeout=60)
        result.stdout=result.stdout.decode('utf-8');result.stderr=result.stderr.decode('utf-8',errors='replace')
        return result
    owner=os.getenv('NSAI_TEST_PRIVATE_OWNER') or uuid4().hex
    assert len(owner)==32 and all(c in '0123456789abcdef' for c in owner)
    started = docker('run', '--detach', '--name', name, '--label','nsai.owner='+owner,'--network', 'none',
                     '--memory', '256m', '--cpus', '1', '--tmpfs',
                     '/var/lib/postgresql/data:rw,noexec,nosuid,size=192m',
                     '-e', 'POSTGRES_HOST_AUTH_METHOD=trust', '-e', 'POSTGRES_DB=nsai',
                     os.getenv('NSAI_TEST_PRIVATE_DATABASE_IMAGE', 'postgres:16-alpine'))
    assert started.returncode == 0, started.stderr
    try:
        for _ in range(100):
            # The entrypoint's temporary initialization server uses only a
            # Unix socket; TCP readiness identifies the final server.
            if docker('exec', name, 'pg_isready', '-h', '127.0.0.1', '-U', 'postgres').returncode == 0:
                break
            time.sleep(.1)
        else:
            pytest.fail('Owned PostgreSQL did not become ready')
        def sql(body, *, app=False, actor=None, role='operator', job=None, ok=True, database_name='nsai'):
            assert database_name in {'nsai','nsai_restored'}
            context = ''
            if actor is not None:
                # Test identities are fixed fixture values, not user input.
                assert actor.replace('-','').replace('_','').isalnum()
                assert role in {'operator','viewer','reviewer','admin'}
                context = f"SET nsai.actor='{actor}'; SET nsai.role='{role}';\n"
            if job is not None:
                import re
                from uuid import UUID
                assert re.fullmatch('[a-f0-9]{64}',job['id'])
                assert str(UUID(job['lease_token']))==job['lease_token']
                context+=f"SET nsai.job_id='{job['id']}'; SET nsai.job_lease='{job['lease_token']}';\n"
            result = docker('exec', '-i', name, 'psql', '-X', '-qAt', '-v',
                            'ON_ERROR_STOP=1', '-U', 'postgres', '-d', database_name,
                            input=('SET ROLE nsai_app;\n' if app else '') + context + body)
            if ok is None:
                return result
            if ok:
                assert result.returncode == 0, result.stderr
            else:
                assert result.returncode != 0, 'Expected database rejection'
            return result.stdout.strip()
        spec = importlib.util.spec_from_file_location('private_test_migrate', ROOT/'scripts/migrate.py')
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)
        script = migration.migration_sql(ROOT) + migration.role_sql('x'*48)
        sql(script)
        sql(script)  # journal replay and privilege convergence
        # The source and its immutable owner must be inserted in the same
        # transaction/connection. Each psql call is a separate connection.
        sql("INSERT INTO documents(id,title,source_version,sha256,raw_text) VALUES "
            "('legacy','Legacy','1','bbb','legacy');")
        sql("BEGIN; INSERT INTO documents(id,title,source_version,sha256,raw_text,owner_scope,ingested_by) VALUES "
            "('private','Private','1','aaa','secret','local-user-alice','local-user-alice'); "
            "COMMIT;", app=True, actor='local-user-alice')
        def run_source_fixture(fixture='private_source_pg_fixture.py'):
            assert fixture in {'private_source_pg_fixture.py','private_derived_pg_fixture.py','private_contract_pg_fixture.py','library_pages_pg_fixture.py','claim_context_pg_fixture.py','audit_lock_pg_fixture.py','claim_pages_small_pg_fixture.py','global_source_budget_pg_fixture.py','global_embedding_budget_pg_fixture.py','global_governed_budget_pg_fixture.py','knowledge_browse_pg_fixture.py','operational_governance_pg_fixture.py','oauth_accounts_pg_fixture.py','oauth_http_pg_fixture.py','structured_sources_pg_fixture.py','conversation_history_pg_fixture.py','learning_pages_pg_fixture.py','claim_review_context_pg_fixture.py','governed_pages_pg_fixture.py','index_controls_pg_fixture.py'}
            client_name=name+'-source-client'
            source_mode=os.getenv('NSAI_TEST_PRIVATE_PACKAGED_SOURCE','0')
            assert source_mode in {'0','1'}
            source_mounts=[]
            if source_mode=='1':
                assert os.environ['NSAI_TEST_PRIVATE_APPLICATION_IMAGE'].startswith('sha256:')
            else:
                source_mounts=['--mount',f'type=bind,source={(ROOT/"src").as_posix()},target=/app/src,readonly',
                    '--mount',f'type=bind,source={(ROOT/"database").as_posix()},target=/app/database,readonly',
                    '--mount',f'type=bind,source={(ROOT/"deploy/init.sql").as_posix()},target=/app/deploy/init.sql,readonly']
            try:
                return docker('run','--rm','--name',client_name,'--label','nsai.owner='+owner,'--network','container:'+name,
                    '--read-only','--cap-drop','ALL','--security-opt','no-new-privileges',
                    '--pids-limit','64','--memory','512m','--cpus','1',
                    '--tmpfs','/tmp:rw,nosuid,noexec,size=32m,mode=1777',
                    *source_mounts,
                    '--mount',f'type=bind,source={(ROOT/"tests"/fixture).as_posix()},target=/qualification.py,readonly',
                    '--mount',f'type=bind,source={(ROOT/"tests/semantic_fixture_helpers.py").as_posix()},target=/semantic_fixture_helpers.py,readonly',
                    '--mount',f'type=bind,source={(ROOT/"tests/xlsx_fixture_helpers.py").as_posix()},target=/xlsx_fixture_helpers.py,readonly',
                    '--entrypoint','python',os.getenv('NSAI_TEST_PRIVATE_APPLICATION_IMAGE','nsai-implementation-candidate:local'),'/qualification.py')
            finally:
                docker('rm','--force',client_name)
        sql.run_source_fixture=run_source_fixture
        def restore_into_fresh_database():
            dump=docker('exec',name,'pg_dump','-U','postgres','-d','nsai')
            assert dump.returncode==0,dump.stderr
            created=docker('exec',name,'createdb','-U','postgres','nsai_restored')
            assert created.returncode==0,created.stderr
            restored=docker('exec','-i',name,'psql','-X','-q','-v','ON_ERROR_STOP=1',
                            '-U','postgres','-d','nsai_restored',input=dump.stdout)
            assert restored.returncode==0,restored.stderr
            # pg_dump without --create does not capture database-level ACLs.
            # Match deployment's explicit CONNECT grant on this fresh DB name.
            sql('GRANT CONNECT ON DATABASE nsai_restored TO nsai_app;')
            return lambda body,**options:sql(body,database_name='nsai_restored',**options)
        sql.restore_into_fresh_database=restore_into_fresh_database
        yield sql
    finally:
        # Only remove the uniquely named, ephemeral container created above.
        docker('rm', '--force', name)


def test_private_owner_legacy_quarantine_and_no_role_bypass(database):
    for actor, expected in [('local-user-alice', 't'), ('local-user-bob', 'f'),
                            ('local-admin', 'f'), ('learning-agent', 'f')]:
        assert database(f"SELECT nsai_private_can_read('private','{actor}');", app=True) == expected
    assert database("SELECT nsai_private_can_read('legacy','local-user-alice');", app=True) == 'f'
    assert database("SELECT nsai_private_can_read('missing','local-user-alice');", app=True) == 'f'
    database("SELECT nsai_private_own('legacy','local-user-alice');", app=True, ok=False)


def test_owner_immutable_and_no_direct_application_policy_writes(database):
    database("UPDATE document_owners SET owner_actor='local-user-bob';", ok=False)
    database("DELETE FROM private_access_events;", ok=False)
    for table in ['document_owners', 'document_policy_versions', 'document_read_grants',
                  'private_groups', 'private_group_members', 'private_access_events']:
        database(f'SELECT * FROM {table};', app=True, ok=False)
        database(f'DELETE FROM {table};', app=True, ok=False)
    database("SELECT nsai_private_membership('team','local-user-bob','local-admin',1,false);",
             app=True, ok=False)
    database('SELECT last_value FROM private_access_events_id_seq;', app=True, ok=False)


def test_shares_cas_revocation_and_reader_cannot_delegate(database):
    assert database("SELECT nsai_private_share('private','local-user-alice',1,'user','local-user-bob',NULL,false);", app=True) == '2'
    assert database("SELECT nsai_private_can_read('private','local-user-bob');", app=True) == 't'
    database("SELECT nsai_private_share('private','local-user-bob',2,'user','local-user-carol',NULL,false);", app=True, ok=False)
    database("SELECT nsai_private_share('private','local-user-alice',1,'user','local-user-carol',NULL,false);", app=True, ok=False)
    assert database("SELECT nsai_private_share('private','local-user-alice',2,'user','local-user-bob',NULL,true);", app=True) == '3'
    assert database("SELECT nsai_private_can_read('private','local-user-bob');", app=True) == 'f'
    assert database("SELECT count(*) FROM private_access_events WHERE document_id='private';") == '3'


def test_membership_removal_and_expired_grants(database):
    database("INSERT INTO private_groups(group_id) VALUES('team');")
    assert database("SELECT nsai_private_membership('team','local-user-carol','local-admin',1,false);") == '2'
    assert database("SELECT nsai_private_share('private','local-user-alice',1,'group','team',NULL,false);", app=True) == '2'
    assert database("SELECT nsai_private_can_read('private','local-user-carol');", app=True) == 't'
    assert database("SELECT nsai_private_membership('team','local-user-carol','local-admin',2,true);") == '3'
    assert database("SELECT nsai_private_can_read('private','local-user-carol');", app=True) == 'f'
    database("SELECT nsai_private_membership('team','local-user-carol','local-admin',2,false);", ok=False)
    database("INSERT INTO document_read_grants VALUES('private','user','local-user-expired',now()-interval '1 second',false);")
    assert database("SELECT nsai_private_can_read('private','local-user-expired');", app=True) == 'f'


def test_source_ownership_and_events_roll_back_together(database):
    database("BEGIN; INSERT INTO documents(id,title,source_version,sha256,raw_text,owner_scope,ingested_by) "
             "VALUES('rollback','Rollback','1','ccc','x','local-user-alice','local-user-alice'); "
             "ROLLBACK;", app=True, actor='local-user-alice')
    assert database("SELECT count(*) FROM documents WHERE id='rollback';") == '0'
    assert database("SELECT count(*) FROM document_owners WHERE document_id='rollback';") == '0'
    assert database("SELECT count(*) FROM private_access_events WHERE document_id='rollback';") == '0'


def test_audit_failure_rolls_back_share_and_epoch(database):
    database("CREATE FUNCTION private_test_audit_failure() RETURNS trigger LANGUAGE plpgsql AS $$ "
             "BEGIN RAISE EXCEPTION 'Owned audit outage'; END $$; "
             "CREATE TRIGGER private_test_audit_failure BEFORE INSERT ON private_access_events "
             "FOR EACH ROW EXECUTE FUNCTION private_test_audit_failure();")
    try:
        database("SELECT nsai_private_share('private','local-user-alice',1,'user','local-user-outage',NULL,false);", app=True, ok=False)
        database("SELECT nsai_private_authorize_read('private','local-user-alice','admin');", app=True, ok=False)
        assert database("SELECT epoch FROM document_policy_versions WHERE document_id='private';") == '1'
        assert database("SELECT nsai_private_can_read('private','local-user-outage');", app=True) == 'f'
    finally:
        database('DROP TRIGGER private_test_audit_failure ON private_access_events; DROP FUNCTION private_test_audit_failure();')


def test_competing_policy_updates_have_exactly_one_winner(database):
    from concurrent.futures import ThreadPoolExecutor
    def share(subject):
        return database("SELECT nsai_private_share('private','local-user-alice',1,'user',"
                        f"'{subject}',NULL,false);", app=True, ok=None)
    with ThreadPoolExecutor(max_workers=2) as workers:
        results = list(workers.map(share, ['local-user-one','local-user-two']))
    assert sorted(r.returncode == 0 for r in results) == [False, True]
    assert 'Stale policy' in next(r.stderr for r in results if r.returncode)
    assert database("SELECT epoch FROM document_policy_versions WHERE document_id='private';") == '2'
    assert database("SELECT count(*) FROM document_read_grants WHERE document_id='private';") == '1'
    assert database("SELECT count(*) FROM private_access_events WHERE event_type='share';") == '1'


def test_privileged_reads_require_explicit_access_and_committed_audit(database):
    database("SELECT nsai_private_authorize_read('private','local-user-admin','admin');", app=True, ok=False)
    assert database("SELECT count(*) FROM private_access_events WHERE event_type='privileged-read';") == '0'
    database("SELECT nsai_private_share('private','local-user-alice',1,'user','local-user-admin',NULL,false);", app=True)
    assert database("SELECT nsai_private_authorize_read('private','local-user-admin','admin');", app=True) == '2'
    assert database("SELECT actor FROM private_access_events WHERE event_type='privileged-read';") == 'local-user-admin'
    database("BEGIN; SELECT nsai_private_authorize_read('private','local-user-admin','admin'); ROLLBACK;", app=True)
    assert database("SELECT count(*) FROM private_access_events WHERE event_type='privileged-read';") == '1'
    database("SELECT nsai_private_share('private','local-user-alice',2,'user','local-user-admin',NULL,true);", app=True)
    database("SELECT nsai_private_authorize_read('private','local-user-admin','admin');", app=True, ok=False)


def test_database_filters_private_sources_before_counts_and_id_probes(database):
    assert database('SELECT count(*) FROM documents;', app=True) == '1'
    assert database('SELECT count(*) FROM documents;', app=True, actor='local-user-alice') == '1'
    assert database('SELECT count(*) FROM documents;', app=True, actor='local-user-bob') == '0'
    for identifier in ['private','missing']:
        assert database(f"SELECT count(*) FROM documents WHERE id='{identifier}';",
                        app=True, actor='local-user-bob') == '0'
