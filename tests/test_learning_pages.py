import os
import pytest
from nsai import store,learning_pages as pages
from test_private_access_database import database

@pytest.mark.parametrize('settings',[dict(limit=0),dict(limit=101),dict(limit=True),dict(state=[]),dict(state='approved'),dict(own='yes')])
def test_invalid_proposal_bounds_fail_before_storage(settings):
 with store.identity_context(dict(actor='local-operator',role='operator')):
  options={'own':True,**settings}
  with pytest.raises(ValueError):pages.page(**options)

def test_proposal_inspection_requires_appropriate_identity():
 with pytest.raises(PermissionError):pages.page()
 for role in ['operator','viewer']:
  with store.identity_context(dict(actor='local-'+role,role=role)):
   with pytest.raises(PermissionError):pages.page()

@pytest.mark.skipif(os.getenv('NSAI_TEST_PRIVATE_DATABASE')!='1',reason='explicit owned PostgreSQL qualification')
def test_all_proposals_remain_reachable_with_actor_and_source_authorization(database):
 result=database.run_source_fixture('learning_pages_pg_fixture.py')
 assert result.returncode==0,result.stdout+result.stderr
 assert '"status": "PASS_SCOPED"' in result.stdout


@pytest.mark.parametrize('arguments',[dict(expected_revision=True,approve=True),dict(expected_revision=1,approve='yes'),dict(expected_revision=1,approve=True,rationale='short'),dict(expected_revision=1,approve=True,rationale=' '*20)])
def test_invalid_review_transition_fails_before_storage(arguments,monkeypatch):
 from nsai import workflow_store as workflows
 def no_storage():raise AssertionError('Invalid transition reached storage')
 monkeypatch.setattr(store,'connect',no_storage)
 with pytest.raises(ValueError):workflows.review_learning('local-reviewer','a'*32,**arguments)
