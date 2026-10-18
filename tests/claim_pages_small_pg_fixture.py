import json
import os
from pathlib import Path
from nsai import claim_pages

secret=Path('/tmp/owned-db-password');secret.write_text('x'*48)
os.environ.update(NSAI_DB_HOST='127.0.0.1',NSAI_DB_NAME='nsai',NSAI_DB_USER='nsai_app',NSAI_DB_PASSWORD_FILE=str(secret))
first=claim_pages.page(limit=1)
assert first['total']==5 and first['summary']['verified_claims']==2
assert first['items'][0]['status']=='superseded'
assert first['summary']['conflict_analysis_complete'] is True
assert first['summary']['active_conflict_groups']==1
assert first['summary']['historical_conflict_groups']==1
assert first['conflicts'][0]['subject']=='motor'
assert len(first['conflicts'][0]['alternatives'])==2
seen=[first['items'][0]['id']];cursor=first['next_cursor']
while cursor:
    current=claim_pages.page(limit=1,cursor=cursor)
    seen.extend(row['id'] for row in current['items']);cursor=current['next_cursor']
assert len(seen)==len(set(seen))==5
print(json.dumps(dict(status='PASS_SCOPED',all_claims_paged=True,exact_quantity_equivalence=True)))
