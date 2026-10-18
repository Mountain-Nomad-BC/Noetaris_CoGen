import json
import os
import pytest
from test_private_access_database import database

pytestmark=pytest.mark.skipif(os.getenv('NSAI_TEST_PRIVATE_DATABASE')!='1',
                             reason='explicit owned PostgreSQL qualification')


@pytest.mark.parametrize('budget',['records','bytes'])
def test_governed_budget_includes_hidden_other_owner_records(database,budget):
    database("INSERT INTO documents(id,title,source_version,sha256,raw_text,owner_scope,ingested_by) "
             "VALUES('bob-quota','Bob quota','1',repeat('b',64),'Bob source','local-user-bob','local-user-bob');",actor='local-user-bob')
    count=2000 if budget=='records' else 8
    payload="jsonb_build_object('fixture',n)" if budget=='records' else "jsonb_build_object('text',repeat('x',16*1024*1024-2048))"
    database("INSERT INTO governed_records(id,kind,author,document_id,source_sha256,payload,source_ids,provenance_complete) "
        f"SELECT md5(n::text)||md5(n::text),'assembly','local-user-bob','bob-quota',repeat('b',64),{payload},ARRAY['bob-quota'],true FROM generate_series(1,{count}) n;")
    result=database.run_source_fixture('global_governed_budget_pg_fixture.py')
    assert result.returncode==0,result.stderr
    assert json.loads(result.stdout.strip().splitlines()[-1])['other_owner_capacity_enforced'] is True
    assert database('SELECT count(*) FROM governed_records;')==str(count)


def test_governed_accounting_tracks_only_committed_rows(database):
    def insert(key):
        return "INSERT INTO governed_records(id,kind,author,document_id,source_sha256,payload,source_ids,provenance_complete) "\
            f"VALUES(repeat('{key}',64),'assembly','local-user-alice','private',repeat('b',64),'{{\"note\":\"candidate\"}}',ARRAY['private'],true) ON CONFLICT DO NOTHING;"
    database(insert('a'),app=True,actor='local-user-alice')
    before=database('SELECT record_count,canonical_bytes FROM governed_storage_usage;')
    database(insert('a'),app=True,actor='local-user-alice')
    database('BEGIN;'+insert('b')+'ROLLBACK;',app=True,actor='local-user-alice')
    assert database('SELECT record_count,canonical_bytes FROM governed_storage_usage;')==before
    database("UPDATE governed_records SET payload='{\"note\":\"larger candidate payload\"}';",ok=False)
    assert database('SELECT record_count=(SELECT count(*) FROM governed_records) AND canonical_bytes=(SELECT sum(octet_length(payload::text)) FROM governed_records) FROM governed_storage_usage;')=='t'
    database('SELECT * FROM governed_storage_usage;',app=True,actor='local-user-alice',ok=False)
    database('DELETE FROM governed_records;',ok=False)
    assert database('SELECT record_count,canonical_bytes FROM governed_storage_usage;')==before
