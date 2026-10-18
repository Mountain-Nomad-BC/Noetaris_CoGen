"""Managed PostgreSQL preserves the packaged access contract and safe roles."""
import importlib.util
from pathlib import Path
import pytest
from nsai.schema_contract import expected_access_contract
ROOT=Path(__file__).resolve().parents[1]
def migration():
    spec=importlib.util.spec_from_file_location('managed_migrate',ROOT/'scripts/migrate.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def test_native_pg18_contract_preserves_all_existing_access_definitions():
    old=expected_access_contract(16);new=expected_access_contract(18)
    assert old['migration_sha256']==new['migration_sha256']
    assert old['query_sha256']==new['query_sha256']
    definitions=dict(new['definitions'])
    additions=[c for c in definitions['constraints'] if c[3].startswith('NOT NULL ')]
    assert additions
    definitions['constraints']=[c for c in definitions['constraints'] if c not in additions]
    assert definitions==old['definitions']

@pytest.mark.parametrize('major',[15,17,19,'18',True])
def test_unqualified_database_versions_are_rejected(major):
    with pytest.raises(RuntimeError):expected_access_contract(major)

def test_managed_role_refuses_privileged_flags_and_keeps_existing_acl():
    m=migration();password='x'*48
    local=m.role_sql(password);managed=m.role_sql(password,database='neondb',managed=True)
    assert 'ALTER ROLE nsai_app NOSUPERUSER' in local
    assert 'ALTER ROLE nsai_app NOSUPERUSER' not in managed
    assert "RAISE EXCEPTION 'Unsafe application role'" in managed
    for privilege in ['rolsuper','rolcreatedb','rolcreaterole','rolreplication','rolbypassrls','NOT rolcanlogin']:
        assert privilege in managed
    assert 'REVOKE ALL ON DATABASE neondb FROM nsai_app' in managed
    assert 'GRANT SELECT,INSERT ON documents,claims' in managed

@pytest.mark.parametrize('database',['neondb; DROP DATABASE nsai','',None,'production-db'])
def test_managed_database_identifiers_are_bounded(database):
    with pytest.raises(ValueError):migration().role_sql('x'*48,database=database,managed=True)
