import os
import pytest
from nsai import store,governed_pages as pages
from test_private_access_database import database

@pytest.mark.parametrize('settings',[
 dict(limit=0),dict(limit=101),dict(limit=True),dict(offset=-1),
 dict(offset=True),dict(kind=[]),dict(state='applied'),dict(offset=1,cursor='cursor'),
])
def test_invalid_governed_navigation_never_opens_storage(settings,monkeypatch):
 def no_storage():raise AssertionError('Invalid navigation opened storage')
 monkeypatch.setattr(store,'connect',no_storage)
 with store.identity_context(dict(actor='local-operator',role='operator')):
  with pytest.raises(ValueError):pages.page(**settings)

def test_governed_navigation_requires_verified_non_job_identity():
 with pytest.raises(PermissionError):pages.page()
 with store.identity_context(dict(actor='local-operator',role='operator',identity_kind='source-job')):
  with pytest.raises(PermissionError):pages.page()

@pytest.mark.parametrize('rationale',[' '*20,'x'*2001,None])
def test_invalid_governed_rationale_does_not_open_storage(rationale,monkeypatch):
 from nsai import governed_store
 def no_storage():raise AssertionError('Invalid review opened storage')
 monkeypatch.setattr(store,'connect',no_storage)
 with pytest.raises(ValueError):governed_store.review('local-reviewer','f'*64,'reviewed',rationale)

@pytest.mark.skipif(os.getenv('NSAI_TEST_PRIVATE_DATABASE')!='1',reason='explicit owned PostgreSQL qualification')
def test_complete_governed_history_review_and_private_revocation(database):
 database("SELECT setval(pg_get_serial_sequence('governed_reviews','id'),9007199254740992,true);")
 result=database.run_source_fixture('governed_pages_pg_fixture.py')
 assert result.returncode==0,result.stdout+result.stderr
 assert '"status": "PASS_SCOPED"' in result.stdout
