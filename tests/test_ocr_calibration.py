import importlib.util
from pathlib import Path
from nsai.ocr_quality import aggregate_error_rates,error_rates,percentile

spec=importlib.util.spec_from_file_location('calibrate_ocr',Path(__file__).resolve().parents[1]/'scripts/calibrate_ocr.py')
calibration=importlib.util.module_from_spec(spec);spec.loader.exec_module(calibration)

def test_frozen_corpus_counts_splits_and_unsupported_formula():
    labels=[dict(calibration.labels(document,page),family=document,split='development' if document%5==0 else 'holdout') for document in range(50) for page in range(1,5)]
    assert len(labels)==200
    assert len({l['family'] for l in labels})==50
    assert sum(l['split']=='holdout' for l in labels)==160
    assert sum(not l.get('supported',True) for l in labels)==50

def test_micro_average_preserves_denominators():
    result=aggregate_error_rates([error_rates('a','b'),error_rates('a'*99,'a'*99)])
    assert result['cer']==.01
    assert percentile([1,2,3,4,5],95)==5
    assert aggregate_error_rates([error_rates('','bad')])['cer'] is None

def test_critical_sign_decimal_and_negation_are_not_repaired():
    label=dict(reference='Do not exceed -5 C. Gap is 0.5 mm.',critical=['not','-5','0.5','mm'])
    run=dict(result=dict(raw_text='Do exceed 5 C. Gap is 5 mm.',complete=True,ocr_words=[]))
    measured=calibration.evaluate_record(label,run)
    assert measured['critical_exact']==1
    assert measured['critical_total']==4
    assert measured['critical_exact_rate']==.25
