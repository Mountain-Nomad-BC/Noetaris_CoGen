"""Owned real-database structured source custody, sharing and rollback checks."""
import json
import os
from copy import deepcopy
from pathlib import Path
from nsai import store,workflow_store as workflows
from nsai.ingestion import parse_source
from nsai.table_analysis import analyze_source,TableAnalysisInput
from semantic_fixture_helpers import configure_authority,publish_pending
from xlsx_fixture_helpers import workbook

os.environ.update(NSAI_DB_HOST='127.0.0.1',NSAI_DB_NAME='nsai',NSAI_DB_USER='nsai_app')
secret=Path('/tmp/db-secret');secret.write_text('x'*48,encoding='utf-8')
os.environ['NSAI_DB_PASSWORD_FILE']=str(secret)
configure_authority()
identity=lambda name:dict(actor='local-user-'+name,role='operator',identity_kind='local-user',permissions=['ingest','read','chat'])
original=b'product,revenue\r\nsynthetic-revenue,001\r\n"  spaced  ",0\r\n,\r\n'
parsed=parse_source(original,'business.csv')
with store.identity_context(identity('alice')):
    first=workflows.persist_source('Private revenue table','1',original,parsed,'local-user-alice')
    source=first['document_id']
    assert workflows.original_source(source)==(original,'text/csv')
    assert not workflows.persist_source('Duplicate','1',original,parsed,'local-user-alice')['created']
    analysis=analyze_source(source,TableAnalysisInput(value_column=2,skip_rows=1,unit='USD'))
    assert analysis['groups'][0]['value']=='1'
    assert analysis['coverage']['excluded_records']==1
    assert analysis['source_dependencies']==[source] and analysis['revision']=='1'
    with store.connect() as conn:
        manifest=conn.execute('SELECT manifest FROM documents WHERE id=%s',(source,)).fetchone()[0]
        assert manifest['documents'][0]['metadata']['structured_data']==parsed['structured_data']
        assert manifest['documents'][0]['metadata']['normalization_map']==parsed['normalization_map']
        assert conn.execute('SELECT count(*) FROM source_spans WHERE document_id=%s',(source,)).fetchone()[0]==4
    altered=deepcopy(parsed);altered['structured_data']['rows'][1]['cells'][1]['value']='1'
    try:workflows.persist_source('Forged','2',original,altered,'local-user-alice')
    except ValueError:pass
    else:raise AssertionError('Altered table persisted')
    with store.connect() as conn:
        assert conn.execute("SELECT count(*) FROM documents WHERE source_version='2'").fetchone()[0]==0
    json_original=b'{"zero":0,"missing":null,"false":false,"decimal":-0.100e+2,"empty":[]}'
    json_parsed=parse_source(json_original,'source.json')
    json_source=workflows.persist_source('Private typed JSON','1',json_original,json_parsed,'local-user-alice')['document_id']
    assert workflows.original_source(json_source)==(json_original,'application/json')
    with store.connect() as conn:
        manifest=conn.execute('SELECT manifest FROM documents WHERE id=%s',(json_source,)).fetchone()[0]
        assert manifest['documents'][0]['metadata']['structured_data']==json_parsed['structured_data']
    xlsx_original=workbook();xlsx_parsed=parse_source(xlsx_original,'source.xlsx')
    xlsx_source=workflows.persist_source('Private workbook','1',xlsx_original,xlsx_parsed,'local-user-alice')['document_id']
    assert workflows.original_source(xlsx_source)==(xlsx_original,xlsx_parsed['media_type'])
    assert analyze_source(xlsx_source,TableAnalysisInput(value_column=1,sheet='Visible'))['groups'][0]['value']=='1.2300'
    try:analyze_source(xlsx_source,TableAnalysisInput(value_column=2,sheet='Visible'))
    except ValueError:pass
    else:raise AssertionError('Unverified cached formula was used as numeric evidence')
publish_pending()
with store.identity_context(identity('alice')):
    hits=workflows.retrieve('synthetic revenue')
    assert any(hit['document_id']==source for hit in hits)
with store.identity_context(identity('bob')):
    assert not workflows.retrieve('synthetic revenue')
    try:workflows.original_source(source)
    except LookupError:pass
    else:raise AssertionError('Private original leaked')
    try:analyze_source(source,TableAnalysisInput(value_column=2,skip_rows=1))
    except LookupError:pass
    else:raise AssertionError('Private analysis leaked')
    try:workflows.original_source(json_source)
    except LookupError:pass
    else:raise AssertionError('Private JSON leaked')
    try:analyze_source(xlsx_source,TableAnalysisInput(value_column=1,sheet='Visible'))
    except LookupError:pass
    else:raise AssertionError('Private workbook analysis leaked')
print(json.dumps(dict(status='PASS_SCOPED',original_bytes_preserved=True,structured_manifest_preserved=True,
    idempotent=True,foreign_read_denied=True,forged_cells_rejected_before_write=True,
    published_retrieval=True,private_analysis_isolated=True,synthetic_encoder=True,semantic_quality_qualified=False)))
