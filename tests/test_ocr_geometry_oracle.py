import importlib.util
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('geometry_oracle',Path(__file__).resolve().parents[1]/'scripts/qualify_ocr_geometry.py');oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)

def test_independent_known_rectangle_overlap():
    assert oracle.overlap([0,0,10,10],[5,0,15,10])==pytest.approx(1/3)
    assert oracle.overlap([0,0,10,10],[10,0,20,10])==0

def test_exact_text_spatial_pairing_retains_extra_prediction():
    labels=[dict(page=1,text='Pump',ink_box=[0,0,10,10])]
    predictions=[dict(page=1,text='PUMP',pixel_box=[100,100,110,110]),dict(page=1,text='Pump',pixel_box=[0,0,10,10])]
    result=oracle.evaluate(labels,predictions)
    assert result['joint_text_geometry_matches']==1 and len(result['unmatched_predictions'])==1 and result['text_precision']==.5

def test_wrong_text_and_other_page_never_count_as_matches():
    result=oracle.evaluate([dict(page=1,text='not',ink_box=[0,0,10,10])],[dict(page=1,text='now',pixel_box=[0,0,10,10]),dict(page=2,text='not',pixel_box=[0,0,10,10])])
    assert len(result['unmatched_truth'])==1 and len(result['unmatched_predictions'])==2 and result['text_matches']==0

def test_correct_text_with_bad_geometry_is_retained_failure():
    result=oracle.evaluate([dict(page=1,text='Pump',ink_box=[0,0,10,10])],[dict(page=1,text='Pump',pixel_box=[8,0,18,10])])
    assert result['text_matches']==1 and result['joint_text_geometry_matches']==0 and not result['pairs'][0]['geometry_pass']
