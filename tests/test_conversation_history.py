import os
import pytest
from nsai import conversation_history as history
from test_private_access_database import database

@pytest.mark.parametrize('value',['0','-1','1.5','1e2','9223372036854775808',True,1])
def test_message_positions_never_round_or_coerce(value):
    with pytest.raises(ValueError):history._number(value)

def test_large_message_id_is_exact_and_bounds_are_explicit():
    assert history._number('9007199254740993')==9007199254740993
    for value in [True,0,51,1.5]:
        with pytest.raises(ValueError):history._limit(value)
    with pytest.raises(PermissionError):history.sessions()

@pytest.mark.skipif(os.getenv('NSAI_TEST_PRIVATE_DATABASE')!='1',reason='explicit owned PostgreSQL qualification')
def test_durable_history_retention_owner_and_revocation(database):
    database("SELECT setval(pg_get_serial_sequence('session_messages','id'),9007199254740992,true);")
    result=database.run_source_fixture('conversation_history_pg_fixture.py')
    assert result.returncode==0,result.stderr
    assert '"status": "PASS_SCOPED"' in result.stdout
