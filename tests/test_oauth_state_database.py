import os
import pytest
from test_private_access_database import database

pytestmark = pytest.mark.skipif(os.getenv('NSAI_TEST_PRIVATE_DATABASE') != '1',
                               reason='explicit owned PostgreSQL qualification')


def put(database, state='a', browser='b'):
    return database(f"SELECT nsai_oauth_state_put(repeat('{state}',64),repeat('{browser}',64),'state-data');", app=True)


def take(database, state='a', browser='b'):
    return database(f"SELECT coalesce(nsai_oauth_state_take(repeat('{state}',64),repeat('{browser}',64)),'absent');", app=True)


def test_browser_binding_and_single_use_survive_separate_connections(database):
    put(database)
    assert take(database, browser='c') == 'absent'
    assert take(database) == 'state-data'
    assert take(database) == 'absent'
    assert database('SELECT count(*) FROM oauth_pending_states;') == '0'


def test_expired_state_cannot_authenticate_and_new_state_cleans_expiry(database):
    put(database)
    database("UPDATE oauth_pending_states SET expires_at=clock_timestamp()-interval '1 second';")
    assert take(database) == 'absent'
    put(database, state='c')
    assert database('SELECT count(*) FROM oauth_pending_states;') == '1'


def test_individuals_and_roles_cannot_read_or_consume_authentication_state(database):
    put(database)
    for actor, role in [('local-user-alice', 'operator'), ('local-admin', 'admin')]:
        database('SELECT * FROM oauth_pending_states;', app=True, actor=actor, role=role, ok=False)
        database("SELECT nsai_oauth_state_take(repeat('a',64),repeat('b',64));",
                 app=True, actor=actor, role=role, ok=False)
    assert take(database) == 'state-data'


def test_browser_state_capacity_and_conflicting_reuse_do_not_overwrite(database):
    put(database)
    database("SELECT nsai_oauth_state_put(repeat('a',64),repeat('c',64),'changed');", app=True, ok=False)
    for key in 'cdef012':
        put(database, state=key)
    database("SELECT nsai_oauth_state_put(repeat('3',64),repeat('b',64),'extra');", app=True, ok=False)
    assert take(database) == 'state-data'
