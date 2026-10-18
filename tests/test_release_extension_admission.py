"""Release gate must not silently ignore the appended user requirements."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
from datetime import datetime,timezone

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('extension_gate',ROOT/'scripts/check_release_readiness.py')
guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)


@pytest.fixture
def accepted():
    plan=json.loads((ROOT/'plans/implementation/release-validation-extension.json').read_bytes())
    payload=dict(schema_version='nsai.release-extension-acceptance/1',
        extension_sha256=guard.digest((ROOT/'plans/implementation/release-validation-extension.json').read_bytes()),
        reference_plan_sha256='f'*64,independent_review=True,reviewer='separate-verifier',
        requirements=[dict(id=r['id'],disposition='NOT_APPLICABLE' if r['section'] in (9,12) else 'PASS',
                           evidence_id='original-fixture-receipt',reason='Deferred feature excluded from this CPU-only release.') for r in plan['requirements']],
        reference_cards=[dict(id=f'REF-{n:02d}',accepted=True,evidence_id='original-reference-receipt') for n in range(1,10)])
    return plan,payload


def test_complete_scoped_acceptance_payload_passes(accepted):
    plan,payload=accepted
    assert guard.validate_extension_acceptance(plan,payload,reference_plan_sha256='f'*64)==[]


def test_missing_or_duplicate_requirements_fail(accepted):
    plan,payload=accepted
    payload['requirements'].pop()
    assert guard.validate_extension_acceptance(plan,payload,reference_plan_sha256='f'*64)
    payload['requirements'].append(copy.deepcopy(payload['requirements'][0]))
    assert guard.validate_extension_acceptance(plan,payload,reference_plan_sha256='f'*64)


def test_p0_cannot_be_excluded_as_optional(accepted):
    plan,payload=accepted
    payload['requirements'][0]['disposition']='NOT_APPLICABLE'
    assert guard.validate_extension_acceptance(plan,payload,reference_plan_sha256='f'*64)


def test_unverified_requirement_or_missing_reviewer_fails(accepted):
    plan,payload=accepted
    payload['independent_review']=False
    assert guard.validate_extension_acceptance(plan,payload,reference_plan_sha256='f'*64)
    payload['independent_review']=True
    payload['requirements'][0]['disposition']='BLOCKED'
    assert guard.validate_extension_acceptance(plan,payload,reference_plan_sha256='f'*64)


def test_missing_research_card_fails(accepted):
    plan,payload=accepted
    payload['reference_cards'].pop()
    assert guard.validate_extension_acceptance(plan,payload,reference_plan_sha256='f'*64)


def test_changed_planning_binding_fails(accepted):
    plan,payload=accepted
    payload['reference_plan_sha256']='e'*64
    assert guard.validate_extension_acceptance(plan,payload,reference_plan_sha256='f'*64)
    payload['reference_plan_sha256']='f'*64
    payload['extension_sha256']='a'*64
    assert guard.validate_extension_acceptance(plan,payload,reference_plan_sha256='f'*64)


def test_complete_guard_requires_extension_even_when_other_gates_have_fixture_receipts(tmp_path,accepted):
    """Synthetic admission mechanism test; fixture receipts are not genuine release evidence."""
    plan,payload=accepted
    def write(relative,value):
        path=tmp_path/relative;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(value,sort_keys=True),encoding='utf-8')
        return path.read_bytes()
    backlog_raw=(ROOT/'plans/implementation/backlog.json').read_bytes()
    backlog=json.loads(backlog_raw)
    path=tmp_path/'plans/implementation/backlog.json';path.parent.mkdir(parents=True);path.write_bytes(backlog_raw)
    ledger=json.loads((ROOT/'plans/implementation/execution-status.json').read_bytes())
    for card in ledger['cards']:
        card['accepted']=True;card['unaccepted_dependencies']=[]
        for criterion in card['criteria']:criterion['status']='CONFIRMED'
    ledger_raw=write('plans/implementation/execution-status.json',ledger)
    path=tmp_path/'plans/implementation/release-validation-extension.json'
    path.write_bytes((ROOT/'plans/implementation/release-validation-extension.json').read_bytes())
    reference=tmp_path/'docs/implementation/REFERENCE_RESEARCH_EXTENSION.md'
    reference.parent.mkdir(parents=True);reference.write_text('Synthetic independent reference plan fixture',encoding='utf-8')
    snapshot=guard.source_snapshot(tmp_path)
    source_hash=guard.digest(json.dumps(snapshot,sort_keys=True,separators=(',',':')).encode())
    identity=dict(run_id='fixture-only-123',source_sha256=source_hash,image_digest='a'*64,effective_config_sha256='b'*64,producer_sha256='c'*64)
    def receipt(raw,scope):return dict(**identity,status='PASS',exit_code=0,scope=scope,evidence_sha256=guard.digest(raw),captured_at=datetime.now(timezone.utc).isoformat())
    required=[f'NSAI-{n:03d}' for n in range(1,33)]
    foundation=write('evidence/implementation/release-foundation.json',dict(independent_review=True,source_sha256=source_hash,accepted_cards=required,all_original_criteria_and_dependencies_accepted=True))
    artifact=write('evidence/implementation/canonical-security-scan-artifact.json',dict(synthetic_fixture=True))
    security=write('evidence/implementation/release-canonical-security-scan.json',dict(independent_review=True,source_sha256=source_hash,canonical=True,verdict='PASS',unresolved_required_findings=0,canonical_artifact_sha256=guard.digest(artifact)))
    payload['reference_plan_sha256']=guard.digest(reference.read_bytes());payload['source_sha256']=source_hash
    extension=write('evidence/implementation/release-extension-acceptance.json',payload)
    write('evidence/implementation/release-admission.json',dict(backlog_sha256=guard.digest(backlog_raw),ledger_sha256=guard.digest(ledger_raw),source_hashes=snapshot,identity=identity,
        foundation=dict(receipt=receipt(foundation,'runtime')),**{'canonical-security-scan':dict(receipt=receipt(security,'static')),'release-extension':dict(receipt=receipt(extension,'quality'))}))
    assert guard.validate(tmp_path)['status']=='ADMITTED'
    (tmp_path/'evidence/implementation/release-extension-acceptance.json').unlink()
    assert guard.validate(tmp_path)['status']=='DENY'
