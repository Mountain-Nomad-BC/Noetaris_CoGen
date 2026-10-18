import pytest
from nsai.issue_assembly import build_engineering_flow

def flow(lines):
    return build_engineering_flow(document_id='a'*32,revision='1',source_sha256='b'*64,spans=[dict(locator=f'line:{i+1}',text=t) for i,t in enumerate(lines)])

def test_engineering_flow_preserves_sources_and_uncertainty():
    result=flow(['Motor stops when hot.','Observed 85 C at sensor.','Suspect poor cooling.','Check airflow?'])
    assert len(result['nodes'])==4 and result['edges']
    assert result['nodes'][1]['quantities'][0]['value']=='85'
    assert result['nodes'][1]['quantities'][0]['instrument']=='unknown'
    assert result['nodes'][0]['raw_text']=='Motor stops when hot.'
    assert not result['diagnosis_verified'] and not result['flow_execution']
    assert all(not e['causality_verified'] for e in result['edges'])

def test_negation_not_verified_outcome():
    result=flow(['Issue not resolved.'])
    assert 'negated' in result['nodes'][0]['categories']
    assert result['nodes'][0]['state']=='candidate'

def test_flow_limit_explicit_and_deterministic():
    result=flow(['Reported issue']*100)
    assert len(result['nodes'])==60 and result['limitations']
    assert flow(['Observed 12 V'])==flow(['Observed 12 V'])

def test_missing_source_identity_denied():
    with pytest.raises(ValueError):build_engineering_flow(document_id='unknown',revision='1',source_sha256='b'*64,spans=[])

def test_question_quantity_does_not_become_a_measurement():
    result=flow(['Check whether the reading is 85 C?','Suspect overheating.'])
    assert not any(e['relation']=='evidence-review-precedes-hypothesis' for e in result['edges'])

def test_overlapping_categories_cannot_create_a_cycle():
    result=flow(['Observed 85 C and suspect cooling; check fan?','Observed 75 C and suspect flow; check pipe?'])
    edges={(e['source'],e['target']) for e in result['edges']}
    assert not any((b,a) in edges for a,b in edges)
