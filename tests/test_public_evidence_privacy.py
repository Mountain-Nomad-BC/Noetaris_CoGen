import json
from pathlib import Path
import re

def test_public_summary_contains_only_allowlisted_metadata():
    path=Path(__file__).resolve().parents[1]/'assets/verification.json'
    data=json.loads(path.read_text())
    assert set(data)<={'overall_status','captured_at','receipts','central_security','generated_execution','future_providers',
        'deployment_status','limitations','privacy'}
    assert data['overall_status']=='PARTIAL_NOT_CERTIFIED'
    assert data['central_security']=='disabled' and data['generated_execution']=='disabled'
    def check(value):
        if isinstance(value,dict):
            for item in value.values():check(item)
        elif isinstance(value,list):
            for item in value:check(item)
        elif isinstance(value,str):
            assert not re.search(r'(?:[A-Za-z]:[\\/]|/Users/|/home/|Bearer\s|sk-proj-)',value)
    check(data)
    for receipt in data['receipts']:
        assert set(receipt)<={'name','status','exit_code','output_sha256','captured_at','scope'}
