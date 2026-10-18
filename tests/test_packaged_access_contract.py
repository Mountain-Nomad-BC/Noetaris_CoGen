from nsai.schema_contract import expected_access_contract,expected_migrations


def test_packaged_definition_query_and_migrations_match_clean_baseline():
    contract=expected_access_contract()
    assert contract['migration_sha256']==expected_migrations()
    assert len(contract['definitions']['policies'])>=42
    assert len(contract['definitions']['functions'])>=36
    assert contract['definitions']['triggers'] and contract['definitions']['application_acl']
    # SQL passes through a UTF-8 byte pipe on every supported host. Native
    # Windows text-mode translation must not change stored function bodies.
    assert all('\r' not in definition for definition in contract['definitions']['functions'])
