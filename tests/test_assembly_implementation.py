"""Original contract fixtures; pure verification uses no private corpus or operational state."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
import pytest
from nsai.assembly import AssemblyNode, AssemblyPlan, strict_json, canonical_hash, validate_holdout
from nsai.governance import ProposalRegistry, PendingAction, ApprovalProof, decide_local_action, staged_central_decision
from nsai.transcript import bind_turns, classify_turn, request_answer_links
from nsai.operations_metrics import MetricInput, ratio, finite_decimal, ResourceLedger, Reservation
from nsai.ingestion import parse_source

NOW = datetime(2026, 10, 14, 12, tzinfo=timezone.utc)
HASH = 'a' * 64


@pytest.mark.parametrize('raw', ['{"a":1,"a":2}', '{"x":NaN}', '{"x":Infinity}', '{"x":1e999}', '[[[[[0]]]]]'])
def test_strict_json_rejects_ambiguous_nonfinite_deep_inputs(raw):
    with pytest.raises(ValueError): strict_json(raw, max_depth=3)


def test_json_unicode_and_structural_byte_budgets():
    assert strict_json('{"page":"温度"}') == {'page': '温度'}
    with pytest.raises(ValueError): strict_json('"温度"', max_bytes=4)
    with pytest.raises(ValueError): strict_json('[1,2,3]', max_items=3)


def test_parsed_20kb_txt_envelope_fits_canonical_hash_budget():
    parsed = parse_source(b'x' * 20_000, 'source.txt')
    encoded = json.dumps(parsed, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    assert len(encoded) > 65_536
    assert len(canonical_hash(parsed)) == 64


def test_assembly_order_and_dependency_replay_staleness():
    plan = AssemblyPlan((AssemblyNode('index', 'index', ('parse',)), AssemblyNode('parse', 'parse')))
    assert plan.order == ('parse', 'index')
    parsed = plan.create_receipt('parse', source_sha256=HASH, output={'native_pages': 1}, dependencies={}, generation=1)
    indexed = plan.create_receipt('index', source_sha256=HASH, output={'chunks': ['c1']}, dependencies={'parse': parsed}, generation=1)
    assert plan.require_fresh(indexed, source_sha256=HASH, current={'parse': parsed})
    revised = plan.create_receipt('parse', source_sha256=HASH, output={'native_pages': 2}, dependencies={}, generation=2)
    with pytest.raises(ValueError, match='Stale dependency'): plan.require_fresh(indexed, source_sha256=HASH, current={'parse': revised})
    with pytest.raises(ValueError, match='hash mismatch'): plan.verify_integrity(replace(indexed, output_sha256='b'*64))


@pytest.mark.parametrize('nodes', [
    (AssemblyNode('x', 'python-exec'),),
    (AssemblyNode('x', 'parse', ('missing',)),),
    (AssemblyNode('x', 'parse', ('y',)), AssemblyNode('y', 'index', ('x',))),
    (AssemblyNode('x', 'parse'), AssemblyNode('x', 'index')),
])
def test_assembly_rejects_execution_missing_cycles_and_duplicate_nodes(nodes):
    with pytest.raises(ValueError): AssemblyPlan(nodes)


def test_assembly_refuses_stale_configuration_and_source():
    first = AssemblyPlan((AssemblyNode('p', 'parse'),))
    receipt = first.create_receipt('p', source_sha256=HASH, output={}, dependencies={}, generation=1)
    second = AssemblyPlan((AssemblyNode('p', 'parse', configuration_sha256='c'*64),))
    with pytest.raises(ValueError, match='Stale'): second.require_fresh(receipt, source_sha256=HASH, current={})
    with pytest.raises(TypeError): first.nodes['p'] = AssemblyNode('p', 'index')


def test_independent_source_family_paired_evaluation():
    report = validate_holdout({'training-family'}, {'holdout-family'}, [
        {'case_id':'one','family':'holdout-family','baseline':10,'challenger':7},
        {'case_id':'two','family':'holdout-family','baseline':20,'challenger':18}])
    assert report['mean_delta'] == -2.5 and report['population_significance'] == 'unqualified'
    with pytest.raises(ValueError, match='contamination'): validate_holdout({'shared'}, {'shared'}, [])
    with pytest.raises(ValueError): validate_holdout(set(), {'h'}, [{'case_id':'x','family':'h','baseline':float('nan'),'challenger':0}])


def test_data_only_proposal_dedupe_and_no_authority():
    one = ProposalRegistry.propose(capability='alias-proposal', actor='operator', data={'source':'a','alias':'A'})
    two = ProposalRegistry.propose(capability='alias-proposal', actor='operator', data={'alias':'A','source':'a'})
    assert one == two and one.state == 'proposed'
    with pytest.raises(ValueError): ProposalRegistry.propose(capability='alias-proposal', actor='operator', data={'nested':{'execute':'yes'}})
    with pytest.raises(ValueError): ProposalRegistry.propose(capability='permission-grant', actor='operator', data={})


def action_and_proof():
    action = PendingAction('id', 'extraction-correction', 'operator', HASH, 3, NOW + timedelta(minutes=1))
    proof = ApprovalProof('id', 'reviewer', 3, HASH, True, True)
    return action, proof


def test_structured_action_independence_binding_expiry_and_retry():
    action, proof = action_and_proof()
    assert decide_local_action(action, proof, now=NOW, approved_actor='reviewer')['allowed']
    for altered in (replace(proof, actor='operator'), replace(proof, policy_revision=2), replace(proof, payload_sha256='b'*64), replace(proof, step_up_verified=False)):
        assert not decide_local_action(action, altered, now=NOW, approved_actor='reviewer')['allowed']
    assert not decide_local_action(action, proof, now=NOW+timedelta(minutes=2), approved_actor='reviewer')['allowed']
    assert decide_local_action(action, proof, now=NOW, approved_actor='reviewer', completed_action_ids=frozenset({'id'}))['idempotent']
    with pytest.raises(ValueError): decide_local_action(action, 'yes approve', now=NOW, approved_actor='reviewer')


def test_central_activation_always_denied():
    assert staged_central_decision(requested_provider='remy-rie', enabled=True, authenticated=True)['enabled'] is False
    action, proof = action_and_proof()
    assert not decide_local_action(replace(action,action='central-enable'), proof, now=NOW, approved_actor='reviewer')['allowed']


def synthetic_turns():
    source='What was the limit?\nThe limit is 85 C.\nPreviously it was not 75 C.'
    lines=source.splitlines(); spans=[];cursor=0
    for speaker,text in zip(('requester','responder','requester'),lines):
        spans.append({'speaker':speaker,'start':cursor,'end':cursor+len(text),'text':text});cursor+=len(text)+1
    return source, bind_turns(source, session_id='owned-session', spans=spans)


def test_transcript_original_offsets_and_candidate_answer_link():
    source, turns=synthetic_turns()
    assert all(source[t.start:t.end]==t.text for t in turns)
    assert classify_turn(turns[0])['kind']=='question'
    historical=classify_turn(turns[2]);assert historical['flags']['historical'] and historical['flags']['negated']
    links=request_answer_links(turns)
    assert len(links)==1 and links[0]['quantities'][0]['value']=='85' and links[0]['verified'] is False
    quantity=links[0]['quantities'][0]
    assert source[quantity['start']:quantity['end']]=='85 C'
    assert classify_turn(turns[1])['confidence_probability'] is None


def test_transcript_scope_original_mismatch_and_overlap():
    source, turns=synthetic_turns()
    assert request_answer_links((turns[0],replace(turns[1],session_id='foreign')))==()
    with pytest.raises(ValueError): bind_turns(source,session_id='s',spans=[{'speaker':'x','start':0,'end':3,'text':'bad'}])
    with pytest.raises(ValueError): bind_turns(source,session_id='s',spans=[{'speaker':'x','start':0,'end':5},{'speaker':'y','start':3,'end':6}])


@pytest.mark.parametrize('value', ['NaN','Infinity','1e999',True,'bad'])
def test_finite_metrics_reject_bad_numbers(value):
    with pytest.raises(ValueError): finite_decimal(value)


def metric(value, **kwargs):
    defaults=dict(value=Decimal(value),source_sha256=HASH,cohort='daily',grain='attempt',version='1',observed_at=NOW)
    defaults.update(kwargs);return MetricInput(**defaults)


def test_metrics_zero_unknown_cohort_lineage_and_causality():
    assert ratio(metric('2'),metric('0'),now=NOW)['value'] is None
    assert ratio(metric('2'),metric('3',cohort='weekly'),now=NOW)['state']=='unknown'
    report=ratio(metric('2'),metric('3'),now=NOW)
    assert report['value'].startswith('0.666') and report['causal_attribution']=='not_established'
    assert report['lineage']['denominator']=='3'
    assert ratio(metric('2',observed_at=NOW-timedelta(days=2)),metric('3'),now=NOW)['state']=='unknown'


def test_local_budget_reservation_terminal_idempotency_failure_charge_and_expiry():
    original=ResourceLedger(100,3)
    deadline=NOW+timedelta(seconds=10)
    reserved=original.reserve(id='r1',tokens=60,expires_at=deadline,now=NOW)
    assert original.committed_tokens==0 and reserved.committed_tokens==60
    assert reserved.reserve(id='r1',tokens=60,expires_at=deadline,now=NOW)==reserved
    with pytest.raises(ValueError,match='exhausted'): reserved.reserve(id='r2',tokens=50,expires_at=deadline,now=NOW)
    failed=reserved.settle(id='r1',actual_tokens=20,succeeded=False)
    assert failed.committed_tokens==20 and len(failed.reservations)==1
    assert failed.settle(id='r1',actual_tokens=20,succeeded=False)==failed
    with pytest.raises(ValueError,match='Terminal'): failed.settle(id='r1',actual_tokens=20,succeeded=True)
    second=failed.reserve(id='r2',tokens=30,expires_at=deadline,now=NOW)
    reconciled=second.reconcile_expired(now=deadline)
    assert reconciled.committed_tokens==50 and reconciled.reservations[1].state=='abandoned'
    with pytest.raises(ValueError): ResourceLedger(100,3,(Reservation('negative',-10,deadline),))
