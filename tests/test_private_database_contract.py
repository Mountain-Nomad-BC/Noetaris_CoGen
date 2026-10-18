import json
import os
import pytest
from test_private_access_database import database

pytestmark=pytest.mark.skipif(os.getenv('NSAI_TEST_PRIVATE_DATABASE')!='1',
                             reason='explicit owned PostgreSQL qualification')


@pytest.mark.parametrize('drift',[
    "UPDATE nsai_schema_migrations SET sha256=repeat('0',64) WHERE name='database/migrations/0009_private_source_enforcement.sql';",
    'ALTER TABLE chunks DISABLE ROW LEVEL SECURITY;',
    'ALTER TABLE documents OWNER TO nsai_app;',
    'CREATE ROLE unintended_parent; GRANT unintended_parent TO nsai_app;',
    'ALTER POLICY documents_read ON documents USING (true);',
    'ALTER TABLE documents DISABLE TRIGGER private_source_owner;',
    'GRANT SELECT ON semantic_jobs TO nsai_app;',
    "CREATE OR REPLACE FUNCTION nsai_legacy_context() RETURNS boolean LANGUAGE sql STABLE AS $$ SELECT true $$;",
    'ALTER TABLE documents DROP CONSTRAINT documents_owner_scope_shape;',
    "ALTER TABLE documents ALTER COLUMN owner_scope SET DEFAULT 'local-user-bob';",
    'ALTER TABLE documents ALTER COLUMN title DROP NOT NULL;',
    'ALTER TABLE documents ALTER COLUMN title TYPE varchar(500);',
    'ALTER TABLE documents ALTER COLUMN title TYPE text COLLATE "C";',
    'ALTER TABLE native_semantic_passages DISABLE ROW LEVEL SECURITY;',
],ids=['journal','disabled-rls','table-owner','inherited-role','policy-expression','ownership-trigger','private-table-grant','authorization-function','ownership-constraint','column-default','column-nullability','column-type','column-collation','native-index-rls'])
def test_schema_and_authority_drift_is_rejected_before_content_access(database,drift):
    database(drift)
    result=database.run_source_fixture('private_contract_pg_fixture.py')
    assert result.returncode==0,result.stderr
    report=json.loads(result.stdout.strip().splitlines()[-1])
    assert report['status']=='PASS' and report['content_connection_yielded'] is False
    expected=('Application database schema contract does not match' if drift.startswith('UPDATE nsai_schema') else
              'Application source row security is incomplete' if 'DISABLE ROW LEVEL' in drift else
              'Application database authority is not admitted' if ('OWNER TO' in drift or 'CREATE ROLE' in drift) else
              'Application database access definitions do not match')
    assert report['rejection_reason']==expected
