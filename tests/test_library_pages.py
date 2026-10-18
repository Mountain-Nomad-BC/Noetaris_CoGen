import base64
from datetime import datetime,timezone
import json
import pytest
from nsai import store,library_store as library


def identity(name):return dict(actor='local-user-'+name,role='operator',identity_kind='local-user')


def test_cursor_keeps_timestamp_tie_break_and_is_bound_to_actor_and_filter():
    instant=datetime(2026,10,15,tzinfo=timezone.utc)
    with store.identity_context(identity('alice')):
        scope=library._scope('motor')
        cursor=library._cursor(dict(id='a'*32,created_at=instant),scope)
        assert library._position(cursor,scope)==(instant,'a'*32)
        with pytest.raises(ValueError):library._position(cursor,library._scope('pump'))
    with store.identity_context(identity('bob')):
        with pytest.raises(ValueError):library._position(cursor,library._scope('motor'))


@pytest.mark.parametrize('cursor',['', 'x'*513,'not base64',base64.urlsafe_b64encode(b'[]').decode(),
    base64.urlsafe_b64encode(json.dumps(dict(version=True,scope='scope',created_at='2026-10-15',id='x')).encode()).decode()])
def test_malformed_cursor_fails_before_database_acquisition(monkeypatch,cursor):
    def forbidden():raise AssertionError('Invalid cursor reached database')
    monkeypatch.setattr(store,'connect',forbidden)
    with pytest.raises(ValueError):library.page(cursor=cursor)
