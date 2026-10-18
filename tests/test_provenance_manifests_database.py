import os
import pytest
from test_private_access_database import database

pytestmark=pytest.mark.skipif(os.getenv('NSAI_TEST_PRIVATE_DATABASE')!='1',
                             reason='explicit owned PostgreSQL qualification')


def test_manifest_reference_reauthorizes_every_source_and_never_grants_access(database):
    database("INSERT INTO documents(id,title,source_version,sha256,raw_text,owner_scope,ingested_by) "
             "VALUES('bob','Bob','1','bob-hash','canary','local-user-bob','local-user-bob');",actor='local-user-bob')
    register="SELECT nsai_register_source_manifest(ARRAY['private','bob']);"
    database(register,app=True,actor='local-user-alice',ok=False)
    database("SELECT nsai_register_source_manifest(ARRAY['unknown']);",app=True,ok=False)
    database("SELECT nsai_private_share('bob','local-user-bob',1,'user','local-user-alice',NULL,false);",app=True)
    manifest=database(register,app=True,actor='local-user-alice')
    assert len(manifest)==32
    assert database("SELECT nsai_register_source_manifest(ARRAY['bob','private','bob']);",app=True,actor='local-user-alice')==manifest
    read=f"SELECT nsai_source_manifest_sources('{manifest}');"
    assert database(read,app=True,actor='local-user-alice')=='{bob,private}'
    database(read,app=True,actor='local-user-bob',ok=False)
    database(read,app=True,actor='local-user-admin',role='admin',ok=False)
    database("SELECT nsai_private_share('private','local-user-alice',1,'user','local-user-bob',NULL,false);",app=True)
    assert database(read,app=True,actor='local-user-bob')=='{bob,private}'
    database("SELECT nsai_private_share('private','local-user-alice',2,'user','local-user-bob',NULL,true);",app=True)
    database(read,app=True,actor='local-user-bob',ok=False)
    for statement in ['SELECT * FROM source_dependency_manifests;',
                      "UPDATE source_dependency_manifests SET source_ids=ARRAY[]::text[];",
                      'DELETE FROM source_dependency_manifests;']:
        database(statement,app=True,actor='local-user-alice',ok=False)
    database('DELETE FROM source_dependency_manifests;',ok=False)
