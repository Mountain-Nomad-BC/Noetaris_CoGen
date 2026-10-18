"""Actual bounded claim context; synthetic legacy rows are not capacity acceptance."""
import json
import os
from pathlib import Path
from nsai import api,store,workflow_store as workflow
from nsai.models import conflict_groups

secret=Path('/tmp/owned-db-password');secret.write_text('x'*48)
os.environ.update(NSAI_DB_HOST='127.0.0.1',NSAI_DB_NAME='nsai',NSAI_DB_USER='nsai_app',
                  NSAI_DB_PASSWORD_FILE=str(secret))
hits=[dict(document_id='legacy',locator='line:1',source_segments=[dict(locator='line:2')])]
claims=workflow.claim_context(hits)
assert len(claims)<=4 and len(claims)>=2
assert {claim['value'] for claim in claims}=={'75 C','90 C'}
assert conflict_groups(claims)
assert api.require_current_claim_context(hits,claims) is None
try:api.require_current_claim_context(hits,claims[:-1])
except ValueError as error:assert 'changed during inference' in str(error)
else:raise AssertionError('Changed claim context passed revalidation')
memory_claims=workflow.memory_claims('motor temperature')
assert conflict_groups(memory_claims) and len(memory_claims)<20
assert workflow.claim_context(hits,document_ids=['missing'])==[]
assert workflow.claim_context([])==[]
assert not workflow.claim_context([dict(document_id='private',locator='line:1')])
try:workflow.claim_context([dict(document_id='legacy',locator='line:overflow')])
except RuntimeError as error:assert 'synthesis withheld' in str(error)
else:raise AssertionError('Alternative overflow yielded partial claim context')
try:store.all_claims()
except RuntimeError as error:assert 'exceeds qualified claim capacity' in str(error)
else:raise AssertionError('Reflection received a silently truncated corpus')
from nsai import claim_pages
page=claim_pages.page()
assert len(page['items'])==25 and page['total']==6202 and page['has_more']
assert page['summary']['verified_claims']==1
assert page['summary']['active_conflict_groups'] is None
assert page['summary']['conflict_analysis_complete'] is False
assert all(claim['document_id']=='legacy' for claim in page['items'])
next_page=claim_pages.page(cursor=page['next_cursor'])
assert not ({claim['id'] for claim in page['items']} & {claim['id'] for claim in next_page['items']})
print(json.dumps(dict(status='PASS_SCOPED',returned_claims=len(claims),conflict_preserved=True)))
