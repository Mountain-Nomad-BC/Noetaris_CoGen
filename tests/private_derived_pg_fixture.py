"""Actual route/storage replay; HTTP admission stays closed during integration."""
import json
import os
from pathlib import Path
from nsai import store,workflow_store as workflow,security,api
from nsai.ingestion import parse_source
from fastapi import HTTPException
from semantic_fixture_helpers import configure_authority,publish_pending


def main():
    password=Path('/tmp/owned-db-password');password.write_text('x'*48)
    os.environ.update(NSAI_DB_HOST='127.0.0.1',NSAI_DB_NAME='nsai',NSAI_DB_USER='nsai_app',
                      NSAI_DB_PASSWORD_FILE=str(password))
    configure_authority()
    checks=[]
    def identity(name):
        return dict(actor='local-user-'+name,role='operator',identity_kind='local-user',
                    permissions=sorted(security.ROLES['operator']))
    def check(name,condition):
        if not condition:raise AssertionError(name)
        checks.append(name)
    def ingest(name,text):
        data=text.encode()
        with store.identity_context(identity(name)):
            return workflow.persist_source(name+' source','derived-test',data,parse_source(data,'owned.txt'),'local-user-'+name)['document_id']
    alice=ingest('alice','Pump-X maximum operating temperature is 85 C. Alice manual canary.')
    bob=ingest('bob','Pump-X maximum operating temperature is 75 C. BOB_PRIVATE_CANARY.')
    publish_pending()
    with store.identity_context(identity('bob')):
        with store.connect() as conn:
            conn.execute("SELECT nsai_private_share(%s,%s,1,'user',%s,NULL,false)",(bob,'local-user-bob','local-user-alice'))
    question=api.Question(question='Pump-X maximum operating temperature',request_id='f'*32)
    with store.identity_context(identity('alice')):
        result=api.chat(question,identity('alice'))
        check('real chat includes both authorized sources',{alice,bob}.issubset(result['source_dependencies']))
        check('source canary present only while authorized','BOB_PRIVATE_CANARY' in json.dumps(result))
        check('invocation cache carries complete dependencies',workflow.invocation_status('local-user-alice','f'*32)['response']['provenance_complete'] is True)
        check('same-key replay returns the stored response',api.chat(question,identity('alice'))==result)
        sid=result['session_id']
        check('authorized working memory contains the exchange',bool(workflow.memory_context('local-user-alice',sid)['working']))
        obsolete=dict(result,mode='model_unverified',answer='OBSOLETE_COMPLETION_CANARY',support_policy_version='nsai.answer-support/obsolete')
        old_question=api.Question(question='Historical completion',request_id='e'*32)
        workflow.begin_invocation('local-user-alice',old_question.request_id,dict(mode='chat',**old_question.model_dump()))
        workflow.finish_invocation('local-user-alice',old_question.request_id,obsolete)
        old_status=workflow.invocation_status('local-user-alice',old_question.request_id)
        check('obsolete completion retains inspectable state without answer',old_status['state']=='completed' and old_status['response'] is None)
        try:api.chat(old_question,identity('alice'))
        except HTTPException as error:check('obsolete completion cannot replay or execute a second time',error.status_code==409)
        else:raise AssertionError('Obsolete completion replayed')
        workflow.save_exchange(sid,'Historical question',obsolete,'local-user-alice')
        current_memory=workflow.memory_context('local-user-alice',sid)
        check('obsolete assistant assertion is excluded from synthesis','OBSOLETE_COMPLETION_CANARY' not in json.dumps(current_memory) and current_memory['working_support_policy_omissions']==1)
    with store.identity_context(identity('bob')):
        with store.connect() as conn:
            conn.execute("SELECT nsai_private_share(%s,%s,2,'user',%s,NULL,true)",(bob,'local-user-bob','local-user-alice'))
    with store.identity_context(identity('alice')):
        memory=workflow.memory_context('local-user-alice',sid)
        check('revocation withholds the old working exchange',not memory['working'])
        check('revoked canary absent from memory serialization','BOB_PRIVATE_CANARY' not in json.dumps(memory))
        try:workflow.invocation_status('local-user-alice','f'*32)
        except LookupError:checks.append('revoked invocation response cannot be fetched')
        else:raise AssertionError('Revoked invocation response leaked')
        try:api.chat(question,identity('alice'))
        except HTTPException as error:check('revoked idempotency key cannot rerun or return old content',error.status_code==404)
        else:raise AssertionError('Revoked invocation reran')
        try:api.reauthorize_response_sources([alice,bob])
        except LookupError:checks.append('final response authorization rejects a revoked dependency')
        else:raise AssertionError('Revoked response dependencies allowed')
        audit=workflow.audit_report()
        check('scoped audit never claims global continuity',audit['valid'] is None and audit['scope']=='authorized-subset')
        check('scoped audit omits revoked source payload','BOB_PRIVATE_CANARY' not in json.dumps(audit,default=str))
    print(json.dumps(dict(status='PASS',checks=checks,method='Source-mounted real application route/storage functions with PostgreSQL; HTTP admission remains closed')))


if __name__=='__main__':main()
