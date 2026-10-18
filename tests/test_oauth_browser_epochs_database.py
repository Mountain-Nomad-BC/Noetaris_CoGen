import os
import pytest
from test_private_access_database import database

pytestmark=pytest.mark.skipif(os.getenv('NSAI_TEST_PRIVATE_DATABASE')!='1',reason='explicit owned PostgreSQL qualification')
ACTOR='local-user-oauth-'+'a'*32


def test_logout_cancels_all_browser_sessions_and_pending_flows_without_other_devices(database):
    assert database("SELECT nsai_oauth_browser_epoch(repeat('a',64));",app=True)=='1'
    assert database("SELECT nsai_oauth_browser_epoch(repeat('b',64));",app=True)=='1'
    database(f"SELECT nsai_oauth_bind('google','alice','signup','{ACTOR}');",app=True)
    for token,browser in [('c','a'),('d','a'),('e','b')]:
        database(f"SELECT nsai_oauth_session_create(repeat('{token}',64),repeat('f',64),'{ACTOR}',12,repeat('{browser}',64),1);",app=True)
    database("SELECT nsai_oauth_state_put(repeat('a',64),repeat('a',64),'pending');",app=True)
    assert database("SELECT nsai_oauth_browser_cancel(repeat('a',64));",app=True)=='2'
    for token in ['c','d']:
        assert database(f"SELECT nsai_oauth_session_resolve(repeat('{token}',64)) IS NULL;",app=True)=='t'
    assert database("SELECT nsai_oauth_session_resolve(repeat('e',64))->>'actor';",app=True)==ACTOR
    assert database('SELECT count(*) FROM oauth_pending_states;')=='0'
    assert database("SELECT nsai_oauth_browser_epoch(repeat('a',64));",app=True)=='2'
    database("SELECT nsai_oauth_browser_assert(repeat('a',64),1);",app=True,ok=False)
    assert database("SELECT owner_actor FROM document_owners WHERE document_id='private';")=='local-user-alice'


def test_consumed_callback_cannot_restore_a_session_after_logout(database):
    database("SELECT nsai_oauth_browser_epoch(repeat('a',64));",app=True)
    database("SELECT nsai_oauth_state_put(repeat('a',64),repeat('a',64),'consumed-state');",app=True)
    assert database("SELECT nsai_oauth_state_take(repeat('a',64),repeat('a',64));",app=True)=='consumed-state'
    database("SELECT nsai_oauth_browser_cancel(repeat('a',64));",app=True)
    database(f"BEGIN; SELECT nsai_oauth_browser_assert(repeat('a',64),1); SELECT nsai_oauth_bind('google','alice','signup','{ACTOR}'); COMMIT;",app=True,ok=False)
    assert database('SELECT count(*) FROM oauth_accounts;')=='0'
    assert database('SELECT count(*) FROM oauth_login_sessions;')=='0'


def test_client_roles_and_jobs_cannot_read_or_modify_browser_epochs(database):
    database("SELECT nsai_oauth_browser_epoch(repeat('a',64));",app=True)
    for actor,role in [('local-user-alice','operator'),('local-admin','admin')]:
        database('SELECT * FROM oauth_browser_epochs;',app=True,actor=actor,role=role,ok=False)
        database("SELECT nsai_oauth_browser_epoch(repeat('a',64));",app=True,actor=actor,role=role,ok=False)
        database("SELECT nsai_oauth_browser_cancel(repeat('a',64));",app=True,actor=actor,role=role,ok=False)
