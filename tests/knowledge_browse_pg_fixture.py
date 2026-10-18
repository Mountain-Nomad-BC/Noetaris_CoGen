"""Actual private graph/formula reads across owner, grants and revocation."""
import json
import os
from pathlib import Path
from fastapi import HTTPException
from nsai import api,store,security
from semantic_fixture_helpers import configure_authority,publish_pending

password=Path('/tmp/owned-db-password');password.write_text('x'*48)
os.environ.update(NSAI_DB_HOST='127.0.0.1',NSAI_DB_NAME='nsai',NSAI_DB_USER='nsai_app',NSAI_DB_PASSWORD_FILE=str(password))
configure_authority()
people={name:security.resolve_principal('Bearer '+Path('/tmp/fixture-user-'+name).read_text()) for name in ['alice','bob','admin']}
sources={}
for name in ['alice','bob']:
    with store.identity_context(people[name]):
        sources[name]=api.ingest(api.DocumentInput(title=name+' graph',version='1',text='Source formula E = m*c^2.'),people[name])['document_id']
publish_pending()
with store.identity_context(people['alice']):
    listing=api.browse_knowledge(sources['alice'],kind='formula',q='',offset=0,limit=2,identity=people['alice'])
    assert listing['items'] and listing['authority_granted'] is False
    node_id=listing['items'][0]['id']
for name in ['bob','admin']:
    with store.identity_context(people[name]):
        try:api.browse_knowledge(sources['alice'],kind='all',q='',offset=0,limit=2,identity=people[name])
        except HTTPException as error:assert error.status_code==404
        else:raise AssertionError('Unshared private graph leaked')
with store.identity_context(people['alice']):
    api.source_share(sources['alice'],api.SourceShare(expected_epoch=1,subject_kind='user',subject_id='local-user-bob'),people['alice'])
with store.identity_context(people['bob']):
    detail=api.knowledge_node(sources['alice'],node_id,offset=0,limit=1,identity=people['bob'])
    assert detail['node']['formula_data']['evaluation']=='not_attempted' and detail['authority_granted'] is False
    assert detail['citation']['document_id']==sources['alice'] and detail['total_relationships']>=2
    try:api.knowledge_node(sources['bob'],node_id,offset=0,limit=1,identity=people['bob'])
    except HTTPException as error:assert error.status_code==404
    else:raise AssertionError('Node identity escaped its source boundary')
with store.identity_context(people['alice']):
    api.source_share(sources['alice'],api.SourceShare(expected_epoch=2,subject_kind='user',subject_id='local-user-bob',revoke=True),people['alice'])
with store.identity_context(people['bob']):
    for read in [lambda:api.browse_knowledge(sources['alice'],kind='all',q='',offset=1,limit=2,identity=people['bob']),
                 lambda:api.knowledge_node(sources['alice'],node_id,offset=1,limit=1,identity=people['bob'])]:
        try:read()
        except HTTPException as error:assert error.status_code==404
        else:raise AssertionError('Revoked graph navigation remained readable')
print(json.dumps(dict(status='PASS_SCOPED',owner_shared_reader_revocation=True,admin_has_no_bypass=True,
    node_identity_bound_to_source=True,formula_lineage_unverified=True,private_http_admitted=False)))
