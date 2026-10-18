import os
import pytest
from nsai import store,claim_review as inspection
from test_private_access_database import database

@pytest.mark.parametrize('offset',[-1,2001,True,1.5])
def test_invalid_comparison_page_never_opens_storage(offset,monkeypatch):
 def no_storage():raise AssertionError('Invalid page reached storage')
 monkeypatch.setattr(store,'connect',no_storage)
 with store.identity_context(dict(actor='local-reviewer',role='reviewer')):
  with pytest.raises(ValueError):inspection.detail('a'*32,offset=offset)

@pytest.mark.parametrize('position',['0','-1','9007199254740993.0','9223372036854775808'])
def test_invalid_event_positions_never_round_or_open_storage(position,monkeypatch):
 def no_storage():raise AssertionError('Invalid event position reached storage')
 monkeypatch.setattr(store,'connect',no_storage)
 with store.identity_context(dict(actor='local-reviewer',role='reviewer')):
  with pytest.raises(ValueError):inspection.events('a'*32,before_id=position)

def test_claim_inspection_requires_verified_identity():
 with pytest.raises(PermissionError):inspection.detail('a'*32)

@pytest.mark.skipif(os.getenv('NSAI_TEST_PRIVATE_DATABASE')!='1',reason='explicit owned PostgreSQL qualification')
def test_full_context_atomic_review_scope_events_and_private_revocation(database):
 database("SELECT setval(pg_get_serial_sequence('claim_events','id'),9007199254740992,true);")
 result=database.run_source_fixture('claim_review_context_pg_fixture.py')
 assert result.returncode==0,result.stdout+result.stderr
 assert '"status": "PASS_SCOPED"' in result.stdout
