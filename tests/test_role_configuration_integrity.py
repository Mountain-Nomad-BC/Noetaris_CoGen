"""Synthetic credentials only; no real files, tokens or runtime configuration."""
import pytest
from fastapi import HTTPException
from nsai import security

@pytest.fixture
def configured(monkeypatch):
    values={role:role+'-synthetic-token' for role in security.FILES}
    for role,setting in security.FILES.items():
        monkeypatch.setenv(setting,role)
    def read(path):
        value=values[path]
        if isinstance(value,Exception):
            raise value
        return value
    monkeypatch.setattr(security,'_secret',read)
    return values

@pytest.mark.parametrize('bad',[OSError('unreadable'),RuntimeError('missing'),UnicodeError('encoding'),'','white space','x'*1025,'nonascii\u00e9'])
def test_early_match_cannot_hide_invalid_later_role(configured,bad):
    configured['admin']=bad
    with pytest.raises(HTTPException) as error:
        security.principal('Bearer '+configured['operator'])
    assert error.value.status_code==503

def test_duplicate_roles_fail_closed_even_on_early_match(configured):
    configured['admin']=configured['operator']
    with pytest.raises(HTTPException) as error:
        security.principal('Bearer '+configured['operator'])
    assert error.value.status_code==503

def test_duplicate_nonmatching_roles_fail_configuration_not_identity(configured):
    configured['admin']=configured['reviewer']
    with pytest.raises(HTTPException) as error:
        security.principal('Bearer unknown-synthetic')
    assert error.value.status_code==503

@pytest.mark.parametrize('authorization',[None,'Basic value','Bearer ','Bearer bad space','Bearer \u00e9'])
def test_malformed_bearer_remains_401_without_reading(monkeypatch,configured,authorization):
    monkeypatch.setattr(security,'_secret',lambda path:pytest.fail('Malformed input read configuration'))
    with pytest.raises(HTTPException) as error:
        security.principal(authorization)
    assert error.value.status_code==401

@pytest.mark.parametrize('role',list(security.FILES))
def test_unique_valid_roles_resolve_expected_identity(configured,role):
    result=security.principal('Bearer '+configured[role])
    assert result==dict(actor='local-'+role,role=role,permissions=sorted(security.ROLES[role]))

def test_optional_absent_roles_stay_optional(monkeypatch,configured):
    for setting in list(security.FILES.values())[1:]:
        monkeypatch.delenv(setting)
    assert security.principal('Bearer '+configured['operator'])['role']=='operator'

def test_central_stays_staged():
    assert security.CentralConfiguration().staged()['enabled'] is False
