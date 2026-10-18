import os
import pytest
from test_private_access_database import database

pytestmark=pytest.mark.skipif(os.getenv('NSAI_TEST_PRIVATE_DATABASE')!='1',reason='explicit owned PostgreSQL qualification')
ACTOR='local-user-oauth-'+'a'*32


def signup(database):
    database(f"SELECT nsai_oauth_bind('google','google-alice','signup','{ACTOR}');",app=True)
    database(f"SELECT nsai_oauth_session_create(repeat('a',64),repeat('b',64),'{ACTOR}',12);",app=True)


def test_provider_share_target_is_owner_scoped_existing_and_enabled(database):
    signup(database)
    query=f"SELECT nsai_current_oauth_sharing_target('private','{ACTOR}');"
    assert database(query,app=True,actor='local-user-alice')=='t'
    for actor,role in [('local-user-bob','operator'),('local-user-admin','admin'),('legacy-service','service')]:
        if role=='service':database(query,app=True,ok=False)
        else:database(query,app=True,actor=actor,role=role,ok=False)
    assert database("SELECT nsai_current_oauth_sharing_target('private','local-user-oauth-"+'b'*32+"');",app=True,actor='local-user-alice')=='f'
    assert database("SELECT nsai_current_oauth_sharing_target('private','local-user-bob');",app=True,actor='local-user-alice')=='f'
    database(f"SELECT nsai_current_source_share('private',1,'user','{ACTOR}',NULL,false);",app=True,actor='local-user-alice')
    assert database("SELECT nsai_private_can_read('private',current_setting('nsai.actor'));",app=True,actor=ACTOR)=='t'
    database(f"SELECT nsai_current_source_share('private',2,'user','{ACTOR}',NULL,true);",app=True,actor='local-user-alice')
    assert database("SELECT nsai_private_can_read('private',current_setting('nsai.actor'));",app=True,actor=ACTOR)=='f'
    database('UPDATE oauth_accounts SET enabled=false;')
    assert database(query,app=True,actor='local-user-alice')=='f'


def test_signup_session_ownership_revocation_and_original_owner_preservation(database):
    signup(database)
    assert database("SELECT nsai_oauth_session_resolve(repeat('a',64))->>'actor';",app=True)==ACTOR
    assert database("SELECT nsai_oauth_session_resolve(repeat('a',64)) IS NULL;",app=True,actor='local-user-bob')=='t'
    assert database("SELECT nsai_oauth_session_resolve(repeat('a',64))->>'authority';",app=True,actor=ACTOR)=='provider'
    assert database("SELECT nsai_oauth_session_revoke(repeat('a',64));",app=True,actor='local-user-bob')=='f'
    assert database("SELECT nsai_oauth_session_revoke(repeat('a',64));",app=True,actor=ACTOR)=='t'
    assert database("SELECT nsai_oauth_session_resolve(repeat('a',64)) IS NULL;",app=True)=='t'
    assert database("SELECT owner_actor FROM document_owners WHERE document_id='private';")=='local-user-alice'
    assert database("SELECT count(*) FROM oauth_identity_events WHERE event='session-revoked';")=='1'


def test_explicit_linking_preserves_canonical_registry_actor_and_rejects_account_takeover(database):
    database("SELECT nsai_oauth_bind('google','google-alice','link-registry','local-user-alice');",app=True)
    assert database("SELECT nsai_oauth_bind('google','google-alice','login',NULL)->>'actor';",app=True)=='local-user-alice'
    database("SELECT nsai_oauth_bind('google','google-alice','link-registry','local-user-bob');",app=True,ok=False)
    database("SELECT nsai_oauth_bind('google','other-google','link-registry','local-user-alice');",app=True,ok=False)
    database("SELECT nsai_oauth_bind('google','unknown','login',NULL);",app=True,ok=False)
    database("SELECT nsai_oauth_bind('github','123','signup','local-admin');",app=True,ok=False)
    assert database('SELECT count(*) FROM oauth_accounts;')=='1'
    assert database('SELECT count(*) FROM oauth_bindings;')=='1'
    assert database("SELECT owner_actor FROM document_owners WHERE document_id='private';")=='local-user-alice'


def test_state_expiry_account_shutdown_and_no_direct_or_role_privilege_access(database):
    signup(database)
    for table in ['oauth_accounts','oauth_bindings','oauth_login_sessions','oauth_identity_events']:
        database('SELECT * FROM '+table+';',app=True,actor='local-admin',role='admin',ok=False)
    database("SELECT nsai_oauth_bind('github','123','link-provider','"+ACTOR+"');",app=True,actor=ACTOR,ok=False)
    database("SELECT nsai_oauth_session_create(repeat('c',64),repeat('d',64),'"+ACTOR+"',12);",app=True,actor=ACTOR,ok=False)
    database("UPDATE oauth_accounts SET enabled=false;")
    assert database("SELECT nsai_oauth_session_resolve(repeat('a',64)) IS NULL;",app=True)=='t'
    database("UPDATE oauth_accounts SET enabled=true; UPDATE oauth_login_sessions SET expires_at=clock_timestamp()-interval '1 second';")
    assert database("SELECT nsai_oauth_session_resolve(repeat('a',64)) IS NULL;",app=True)=='t'


def test_failed_signup_transaction_retains_no_partial_identity_or_session(database):
    database(f"BEGIN; SELECT nsai_oauth_bind('google','google-alice','signup','{ACTOR}'); "
             f"SELECT nsai_oauth_session_create(repeat('a',64),repeat('b',64),'{ACTOR}',12); ROLLBACK;",app=True)
    assert database('SELECT count(*) FROM oauth_accounts;')=='0'
    assert database('SELECT count(*) FROM oauth_bindings;')=='0'
    assert database('SELECT count(*) FROM oauth_login_sessions;')=='0'
    assert database('SELECT count(*) FROM oauth_identity_events;')=='0'


def test_packaged_account_session_and_canonical_audit_integration(database):
    result=database.run_source_fixture('oauth_accounts_pg_fixture.py')
    assert result.returncode==0,result.stderr
    import json
    assert json.loads(result.stdout.strip().splitlines()[-1])['audit_failure_rolls_back'] is True


def test_packaged_http_oauth_and_logout_callback_race(database):
    result=database.run_source_fixture('oauth_http_pg_fixture.py')
    assert result.returncode==0,result.stderr
    import json
    assert json.loads(result.stdout.strip().splitlines()[-1])['inflight_callback_logout_race'] is True
