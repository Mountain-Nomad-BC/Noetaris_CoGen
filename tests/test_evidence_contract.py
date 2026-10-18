from datetime import datetime,timezone,timedelta
import hashlib
import importlib.util
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('evidence_contract',Path(__file__).resolve().parents[1]/'scripts/evidence_contract.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
NOW=datetime(2026,10,14,12,tzinfo=timezone.utc)

def fixture():
    expected=dict(run_id='owned-run-123',source_sha256='a'*64,image_digest='sha256:'+'b'*64,
        effective_config_sha256='c'*64,producer_sha256='d'*64)
    data=b'{"measured":"owned fixture"}'
    receipt=dict(expected,status='PASS',scope='runtime',exit_code=0,captured_at=NOW.isoformat(),evidence_sha256=hashlib.sha256(data).hexdigest())
    return expected,data,receipt

def test_exact_fresh_scoped_receipt_never_certifies_release():
    expected,data,receipt=fixture()
    result=module.admit_receipt(receipt,data,expected,now=NOW)
    assert result['status']=='PASS_SCOPED' and result['certification'] is False and result['release_approval'] is False

@pytest.mark.parametrize('key',module.IDENTITY_FIELDS)
def test_missing_or_wrong_run_identity_fails_closed(key):
    expected,data,receipt=fixture();receipt[key]='changed'
    assert module.admit_receipt(receipt,data,expected,now=NOW)['status']=='UNVERIFIED'
    del expected[key]
    assert module.admit_receipt(receipt,data,expected,now=NOW)['status']=='UNVERIFIED'

@pytest.mark.parametrize('change',[dict(status='FAIL'),dict(exit_code=True),dict(exit_code=1),dict(scope='certified'),
    dict(captured_at=(NOW-timedelta(days=2)).isoformat()),dict(captured_at=(NOW+timedelta(seconds=1)).isoformat()),
    dict(captured_at='2026-10-14T12:00:00'),dict(evidence_sha256='0'*64)])
def test_bad_verdict_age_or_evidence_is_rejected(change):
    expected,data,receipt=fixture();receipt.update(change)
    assert module.admit_receipt(receipt,data,expected,now=NOW)['status']=='UNVERIFIED'

def test_changed_evidence_cannot_reuse_successful_receipt():
    expected,data,receipt=fixture()
    assert module.admit_receipt(receipt,data+b' altered',expected,now=NOW)['status']=='UNVERIFIED'

@pytest.mark.parametrize('scope',[{},[],None,True,42])
def test_hostile_scope_types_return_unverified_instead_of_raising(scope):
    expected,data,receipt=fixture();receipt['scope']=scope
    result=module.admit_receipt(receipt,data,expected,now=NOW)
    assert result['status']=='UNVERIFIED'
    assert result['certification'] is False and result['release_approval'] is False
