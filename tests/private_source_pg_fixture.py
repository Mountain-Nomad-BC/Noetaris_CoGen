"""Runs only in an owned container sharing the isolated test DB namespace.

This is source-mounted Python 3.12 integration evidence, not final-image evidence.
"""
import json
import os
from pathlib import Path
from unittest.mock import patch

from nsai import store, workflow_store as workflow, security
from nsai.ingestion import parse_source
from semantic_fixture_helpers import configure_authority,publish_pending


def main():
    secret=Path('/tmp/owned-db-password')
    secret.write_text('x'*48)
    os.environ.update(NSAI_DB_HOST='127.0.0.1',NSAI_DB_NAME='nsai',NSAI_DB_USER='nsai_app',
                      NSAI_DB_PASSWORD_FILE=str(secret))
    configure_authority()
    checks=[]
    def identity(name,role='operator'):
        return dict(actor='local-user-'+name,role=role,identity_kind='local-user',
                    permissions=sorted(security.ROLES[role]))
    def check(name,condition):
        if not condition:raise AssertionError(name)
        checks.append(name)
    def unavailable(identifier):
        try:workflow.source(identifier)
        except LookupError:return True
        return False
    original=b'The engineered motor operating limit is 85 C. Source custody must remain private.'
    parsed=parse_source(original,'owned.txt')
    with store.identity_context(identity('alice')):
        alice=workflow.persist_source('Alice source','owned-1',original,parsed,'local-user-alice')
        check('owner upload creates document and research',alice['created'])
        check('upload returns durable queued status',alice['indexing']['state']=='queued' and not alice['indexing']['ready'])
        check('staged source is absent from lexical results',not workflow.retrieve('motor operating limit'))
        check('same-owner upload idempotent',not workflow.persist_source('Alice source','owned-1',original,parsed,'local-user-alice')['created'])
        with store.connect() as conn:
            connection_id=id(conn)
            check('real transaction binds Alice',conn.execute("SELECT current_setting('nsai.actor')").fetchone()[0]=='local-user-alice')
    publish_pending()
    with store.identity_context(identity('bob')):
        bob=workflow.persist_source('Bob source','owned-1',original,parsed,'local-user-bob')
        check('same bytes different owner create separate logical document',bob['created'] and bob['document_id']!=alice['document_id'])
        check('Bob cannot inspect Alice source',unavailable(alice['document_id']))
        check('Bob original bytes intact',workflow.original_source(bob['document_id'])[0]==original)
        with store.connect() as conn:
            check('same connection reused with Bob authority',id(conn)==connection_id and conn.execute("SELECT current_setting('nsai.actor')").fetchone()[0]=='local-user-bob')
    publish_pending()
    with store.identity_context(identity('bob')):
        hits=workflow.retrieve('motor operating limit')
        check('published lexical retrieval returns own evidence and excludes other owner',bool(hits) and all(hit['document_id']==bob['document_id'] for hit in hits))
    with store.identity_context(identity('alice')):
        check('Alice cannot inspect Bob source',unavailable(bob['document_id']))
        with store.connect() as conn:
            conn.execute("SELECT nsai_private_share(%s,%s,1,'user',%s,NULL,false)",
                         (alice['document_id'],'local-user-alice','local-user-bob'))
    with store.identity_context(identity('bob')):
        check('explicit shared source readable',workflow.original_source(alice['document_id'])[0]==original)
    with store.identity_context(identity('alice')):
        with store.connect() as conn:
            conn.execute("SELECT nsai_private_share(%s,%s,2,'user',%s,NULL,true)",
                         (alice['document_id'],'local-user-alice','local-user-bob'))
    with store.identity_context(identity('bob')):
        check('revoked shared source unavailable',unavailable(alice['document_id']))
    with store.identity_context(identity('admin','admin')):
        check('admin role does not bypass private source',unavailable(alice['document_id']))
    with store.identity_context(identity('alice')):
        with store.connect() as conn:
            conn.execute("SELECT nsai_private_share(%s,%s,3,'user',%s,NULL,false)",
                         (alice['document_id'],'local-user-alice','local-user-admin'))
    with store.identity_context(identity('admin','admin')):
        check('explicitly shared admin can fetch original',workflow.original_source(alice['document_id'])[0]==original)
    check('unbound legacy reader cannot fetch private original',unavailable(alice['document_id']))
    with store.connect() as conn:
        check('legacy lease resets real connection authority',conn.execute("SELECT current_setting('nsai.actor')").fetchone()[0]=='legacy-service')
    with store.identity_context(identity('alice')):
        failed=b'This owned source must roll back with failed research assembly.'
        with patch('nsai.research_store.persist',side_effect=ValueError('Owned fault injection')):
            try:workflow.persist_source('Rollback source','rollback-2',failed,parse_source(failed,'failed.txt'),'local-user-alice')
            except ValueError:pass
            else:raise AssertionError('Expected owned rollback')
        check('failed ingestion leaves no visible source',all(d['title']!='Rollback source' for d in store.all_documents()))
        with store.connect() as conn:
            check('pool usable after rollback',conn.execute("SELECT current_setting('nsai.actor')").fetchone()[0]=='local-user-alice')
    # Test DB accepts loopback connections for owned fixtures. Accidentally
    # supplying owner authority must be rejected before any content query.
    os.environ['NSAI_DB_USER']='postgres'
    try:
        with store.identity_context(identity('bob')):
            try:workflow.original_source(alice['document_id'])
            except RuntimeError:checks.append('misconfigured owner DB connection is rejected before content access')
            else:raise AssertionError('Owner authority bypassed source enforcement')
    finally:os.environ['NSAI_DB_USER']='nsai_app'
    print(json.dumps(dict(status='PASS',method='Source-mounted Python 3.12 application with real PostgreSQL; synthetic encoder for lifecycle only; no live services or model-quality qualification',
                          checks=checks,documents=[alice['document_id'],bob['document_id']])))


if __name__=='__main__':main()
