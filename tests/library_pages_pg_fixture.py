"""Actual route/storage paging in owned PostgreSQL; private HTTP gate stays closed."""
import json
import os
from pathlib import Path
from nsai import api,store,security,workflow_store as workflow
from semantic_fixture_helpers import configure_authority

secret=Path('/tmp/owned-db-password');secret.write_text('x'*48)
os.environ.update(NSAI_DB_HOST='127.0.0.1',NSAI_DB_NAME='nsai',NSAI_DB_USER='nsai_app',NSAI_DB_PASSWORD_FILE=str(secret))
configure_authority()
def identity(name):return security.resolve_principal('Bearer '+Path('/tmp/fixture-user-'+name).read_text())

with store.identity_context(identity('alice')):
    cursor=None;seen=[];pages=0
    while True:
        result=api.documents(limit=25,cursor=cursor,q='Owned source',identity=identity('alice'))
        assert result['total']==120 and len(result['items'])<=25
        assert all(len(item['sha256'])==64 and not item['sha256'].startswith('private/') for item in result['items'])
        seen.extend(item['id'] for item in result['items']);pages+=1
        if pages==1:alice_cursor=result['next_cursor']
        if not result['has_more']:assert result['next_cursor'] is None;break
        assert pages<6;cursor=result['next_cursor']
    assert pages==5 and len(seen)==len(set(seen))==120
    assert seen==sorted(seen,reverse=True)  # every fixture timestamp is identical
    assert api.documents(q='Owned source 00',identity=identity('alice'))['total']==10
    assert api.documents(q='%',identity=identity('alice'))['total']==0
    session=workflow.session(identity('alice')['actor'])
    memory=workflow.memory_context(identity('alice')['actor'],session)
    assert memory['source_manifest_id'] and memory['source_dependency_count']>=120
    assert memory['envelope_bytes']==len(json.dumps(memory,ensure_ascii=False,allow_nan=False).encode())
    assert memory['envelope_bytes']<=16384
    from nsai.source_dependencies import collect_sources
    assert set(seen)<=set(collect_sources(memory))
with store.identity_context(identity('bob')):
    result=api.documents(q='Owned source',identity=identity('bob'))
    assert result['total']==3 and len(result['items'])==3
    try:api.documents(cursor=alice_cursor,q='Owned source',identity=identity('bob'))
    except Exception as error:assert getattr(error,'status_code',None)==400
    else:raise AssertionError('Cross-identity cursor accepted')
print(json.dumps(dict(status='PASS_SCOPED',authorized_sources=120,pages=5,timestamp_ties=True,cross_identity_cursor_rejected=True)))
