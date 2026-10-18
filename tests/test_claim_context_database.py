import json
import os
import pytest
from test_private_access_database import database

pytestmark=pytest.mark.skipif(os.getenv('NSAI_TEST_PRIVATE_DATABASE')!='1',
                             reason='explicit owned PostgreSQL qualification')


def test_duplicates_and_unrelated_corpus_do_not_hide_a_conflicting_witness(database):
    database("DELETE FROM source_index_state WHERE document_id='legacy'; "
             "INSERT INTO claims(id,document_id,subject,predicate,value,locator) "
             "SELECT 'overflow-'||n,'legacy','overflow','temperature',n||' C','line:overflow' FROM generate_series(1,2001) n; "
             "INSERT INTO claims(id,document_id,subject,predicate,value,locator) "
             "SELECT 'duplicate-'||n,'legacy','motor','temperature','75 C','line:2' FROM generate_series(1,2100) n; "
             "INSERT INTO claims(id,document_id,subject,predicate,value,locator) "
             "SELECT 'unrelated-'||n,'legacy','other-'||n,'temperature','25 C','line:3' FROM generate_series(1,2100) n; "
             "INSERT INTO claims(id,document_id,subject,predicate,value,locator) "
             "VALUES('conflict','legacy','motor','temperature','90 C','line:9000'),"
             "('hidden','private','motor','temperature','999 C','line:1'); "
             "INSERT INTO claims(id,document_id,subject,predicate,value,locator,status,reviewed_by,source_ids,provenance_complete) "
             "VALUES('hidden-review','legacy','motor','temperature','9999 C','line:9001','verified','fixture-reviewer',ARRAY['legacy','private'],true); "
             "UPDATE claims SET status='verified',reviewed_by='independent-fixture-reviewer' WHERE id='duplicate-1';")
    result=database.run_source_fixture('claim_context_pg_fixture.py')
    assert result.returncode==0,result.stderr
    assert json.loads(result.stdout.strip().splitlines()[-1])['conflict_preserved'] is True


def test_review_summary_is_independent_of_page_and_preserves_exact_equivalence(database):
    database("DELETE FROM source_index_state WHERE document_id='legacy'; "
        "INSERT INTO claims(id,document_id,subject,predicate,value,locator,status,reviewed_by,created_at) VALUES "
        "('a','legacy','motor','temperature','75 C','line:1','verified','fixture-reviewer','2020-01-01'),"
        "('b','legacy','motor','temperature','90 C','line:2','candidate',NULL,'2020-01-01'),"
        "('c','legacy','pump','temperature','75 C','line:3','verified','fixture-reviewer','2020-01-01'),"
        "('d','legacy','pump','temperature','167 F','line:4','candidate',NULL,'2020-01-01'),"
        "('e','legacy','motor','temperature','95 C','line:5','superseded',NULL,'2020-01-01'),"
        "('hidden','private','motor','temperature','999 C','line:1','candidate',NULL,'2020-01-01');")
    result=database.run_source_fixture('claim_pages_small_pg_fixture.py')
    assert result.returncode==0,result.stderr
    assert json.loads(result.stdout.strip().splitlines()[-1])['exact_quantity_equivalence'] is True


def test_projection_is_private_and_source_jobs_cannot_read_library_claims(database):
    assert database("SELECT has_function_privilege('nsai_app','nsai_readable_claim_projection(text[],text,integer[],boolean)','EXECUTE');")=='f'
    denied=database('SELECT * FROM nsai_readable_claim_projection(NULL,NULL,NULL,true);',app=True,ok=None)
    assert denied.returncode and 'permission denied' in denied.stderr
    job=dict(id='f'*64,lease_token='11111111-1111-4111-8111-111111111111')
    for query in [
        "SELECT * FROM nsai_claim_context('[{\"document_id\":\"legacy\",\"locator\":\"line:1\"}]',NULL,NULL,NULL);",
        "SELECT * FROM nsai_memory_claim_seeds('motor',NULL,NULL,NULL);",
        'SELECT nsai_claim_review_page(25,NULL,NULL);',
        'SELECT * FROM nsai_reflection_claims();',
    ]:
        result=database(query,app=True,job=job,ok=None)
        assert result.returncode and 'Request context required' in result.stderr


def test_claim_context_scope_filters_precede_alternative_selection(database):
    database("DELETE FROM source_index_state WHERE document_id='legacy'; "
        "INSERT INTO claims(id,document_id,subject,predicate,value,locator) VALUES "
        "('p250','legacy','motor','temperature','75 C','page:250:line:1'),"
        "('p1','legacy','motor','temperature','90 C','page:1:line:1'),"
        "('private250','private','motor','temperature','999 C','page:250:line:1');")
    spans='[{"document_id":"legacy","locator":"page:250:line:1"}]'
    def context(selected='NULL',revision='NULL',pages='NULL'):
        return json.loads(database("SELECT coalesce(jsonb_agg(c),'[]'::jsonb) FROM nsai_claim_context('"+spans+"',"+selected+','+revision+','+pages+') c;',app=True))
    assert {r['value'] for r in context()}=={'75 C','90 C'}
    assert {r['value'] for r in context("ARRAY['legacy']","'1'",'ARRAY[250]')}=={'75 C'}
    assert context("ARRAY['private']")==[]
    assert context("ARRAY['legacy']","'stale'")==[]
    invalid=database("SELECT * FROM nsai_claim_context('"+spans+"',NULL,NULL,ARRAY[1001]);",app=True,ok=None)
    assert invalid.returncode and 'Invalid claim scope' in invalid.stderr
