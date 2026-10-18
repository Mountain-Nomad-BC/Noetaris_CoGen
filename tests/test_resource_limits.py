import pytest
from nsai import resource_limits,store


def test_default_limits_are_unchanged_and_returned_values_are_not_mutable_policy(monkeypatch):
    monkeypatch.delenv('NSAI_CAPACITY_PROFILE',raising=False)
    assert resource_limits.capacity_profile()=='default'
    assert resource_limits.capacity_limits()==dict(documents=100,claims=2000,semantic_payload_bytes=128*1024*1024)
    value=resource_limits.capacity_limits();value['documents']=9999
    assert resource_limits.capacity_limits()['documents']==100


def test_larger_reference_profile_requires_explicit_server_selection(monkeypatch):
    monkeypatch.setenv('NSAI_CAPACITY_PROFILE','reference-1000')
    assert resource_limits.capacity_limits()==dict(documents=1000,claims=2000,semantic_payload_bytes=512*1024*1024)


@pytest.mark.parametrize('profile',['','1000','DEFAULT','reference-10000',' reference-1000','reference-1000 '])
def test_unknown_profiles_fail_before_database_configuration_is_read(monkeypatch,profile):
    monkeypatch.setenv('NSAI_CAPACITY_PROFILE',profile)
    monkeypatch.delenv('NSAI_DB_PASSWORD_FILE',raising=False)
    with pytest.raises(ValueError,match='capacity profile'):
        with store.connect():pytest.fail('Invalid profile admitted')
