"""Actual PostgreSQL history retention and current source/owner authorization."""
import json,os
from pathlib import Path
from nsai import store,workflow_store as workflows,conversation_history as history
from semantic_fixture_helpers import configure_authority

secret=Path('/tmp/history-db-password');secret.write_text('x'*48,encoding='utf-8')
os.environ.update(NSAI_DB_HOST='127.0.0.1',NSAI_DB_NAME='nsai',NSAI_DB_USER='nsai_app',NSAI_DB_PASSWORD_FILE=str(secret))
configure_authority()
def who(name):return dict(actor='local-user-'+name,role='operator',identity_kind='local-user',permissions=['read','chat','ingest'])
def unavailable(call):
    try:call()
    except LookupError:return True
    return False
with store.identity_context(who('bob')):
    document=store.store_document('History source','Retained source evidence.','1','local-user-bob')['document_id']
    with store.connect() as conn:conn.execute("SELECT nsai_current_source_share(%s,1,'user','local-user-alice',NULL,false)",(document,))
full_answer='Full retained assistant answer: '+('original exact content '*1200)
with store.identity_context(who('alice')):
    first=workflows.session('local-user-alice')
    workflows.save_exchange(first,'Original question',dict(answer=full_answer,mode='evidence-extract',citations=[],source_dependencies=[document],provenance_complete=True),'local-user-alice')
    second=workflows.session('local-user-alice')
    sessions=history.sessions(limit=1);assert sessions['has_more'] and len(sessions['items'])==1
    assert history.sessions(limit=1,cursor=sessions['next_cursor'])['items'][0]['id']==first
    page=history.messages(first,limit=1);assert page['has_more'] and page['items'][0]['role']=='assistant'
    message_id=page['items'][0]['id'];assert isinstance(message_id,str) and int(message_id)>9007199254740992
    recovered=history.message(first,message_id)
    assert recovered['receipt']['answer']==full_answer and len(recovered['text_preview'])==12000
    older=history.messages(first,limit=1,before_id=message_id)
    assert older['items'][0]['role']=='user' and not older['has_more']
    assert history.message(first,older['items'][0]['id'])['text_preview']=='Original question'
with store.identity_context(who('bob')):
    assert history.sessions()['items']==[] and unavailable(lambda:history.messages(first))
    assert unavailable(lambda:history.message(first,message_id))
    try:history.sessions(cursor=sessions['next_cursor'])
    except ValueError:pass
    else:raise AssertionError('Cross-owner cursor accepted')
    with store.connect() as conn:conn.execute("SELECT nsai_current_source_share(%s,2,'user','local-user-alice',NULL,true)",(document,))
with store.identity_context(who('alice')):
    assert history.messages(first)['items']==[] and unavailable(lambda:history.message(first,message_id))
    assert {row['id'] for row in history.sessions()['items']}=={first,second}
with store.identity_context(who('bob')):
    with store.connect() as conn:conn.execute("SELECT nsai_current_source_share(%s,3,'user','local-user-alice',NULL,false)",(document,))
with store.identity_context(who('alice')):
    assert history.message(first,message_id)['receipt']['answer']==full_answer
operator=dict(actor='local-operator',role='operator',permissions=['read','chat'])
with store.identity_context(operator):
    shared=workflows.session('local-operator')
    workflows.save_exchange(shared,'Legacy role question',dict(answer='Retained own-role answer',mode='evidence-extract',citations=[],source_dependencies=[],provenance_complete=True),'local-operator')
    assert history.messages(shared)['items']
with store.identity_context(dict(actor='local-viewer',role='viewer',permissions=['read'])):
    assert history.sessions()['items']==[] and unavailable(lambda:history.messages(shared))
from fastapi.testclient import TestClient
from nsai import api
for role,variable in [('operator','NSAI_API_TOKEN_FILE'),('viewer','NSAI_VIEWER_TOKEN_FILE')]:
    path=Path('/tmp/history-role-'+role);path.write_text(('owned-role-'+role).ljust(48,'x'),encoding='utf-8');os.environ[variable]=str(path)
with TestClient(api.app) as client:
    operator_headers={'Authorization':'Bearer '+Path(os.environ['NSAI_API_TOKEN_FILE']).read_text(encoding='utf-8')}
    viewer_headers={'Authorization':'Bearer '+Path(os.environ['NSAI_VIEWER_TOKEN_FILE']).read_text(encoding='utf-8')}
    assert client.get('/v1/chat/sessions').status_code==401
    response=client.get('/v1/chat/sessions',headers=operator_headers)
    assert response.status_code==200 and {row['id'] for row in response.json()['items']}=={shared}
    response=client.get('/v1/chat/sessions/'+shared+'/messages',headers=operator_headers)
    assert response.status_code==200 and len(response.json()['items'])==2
    message_id=response.json()['items'][0]['id']
    assert client.get('/v1/chat/sessions/'+shared+'/messages/'+message_id,headers=operator_headers).json()['receipt']['answer']=='Retained own-role answer'
    assert client.get('/v1/chat/sessions/'+shared+'/messages',headers=viewer_headers).status_code==404
    assert client.get('/v1/chat/sessions',headers={'Authorization':'Bearer '+Path('/tmp/fixture-user-alice').read_text(encoding='utf-8')}).status_code==503
print(json.dumps(dict(status='PASS_SCOPED',full_receipt_preserved=True,large_integer_ids_preserved=True,owner_filter=True,revocation_withholds_without_deletion=True,regrant_recovers_original=True,legacy_roles_cannot_read_each_others_history=True)))
