"""Baseline for the current narrow deterministic extractor, NOT AMD model benchmark.

To run from repo root: python evaluations/run_fixture_baseline.py
"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from nsai.models import extract_claims,conflict_groups
fixture=json.loads((ROOT/'evaluations/golden/deterministic_claim_cases.json').read_text())
rows=[];checks=[];by_case={}
for case in fixture['cases']:
    text=(ROOT/'datasets/synthetic'/case['filename']).read_text()
    got=extract_claims(text)
    by_case[case['id']]=got
    ok=([x.value for x in got]==case['expected_values'] and [x.locator for x in got]==case['expected_locators'])
    checks.append({'case':case['id'],'passed':ok,'actual_values':[x.value for x in got],'actual_locators':[x.locator for x in got]})
for pair in fixture['pairwise_conflict_cases']:
    r=[]
    for i,cid in enumerate((pair['left'],pair['right'])):
        for claim in by_case[cid]:
            r.append({'id':f'{cid}_{i}','document_id':cid,'subject':claim.subject,'predicate':claim.predicate,'value':claim.value,'locator':claim.locator})
    conflict=bool(conflict_groups(r))
    checks.append({'case':pair['id'],'passed':conflict==pair['expected_conflict'],'actual_conflict':conflict})
out={'system_under_test':'original-narrow-regex-demo','real_amd_inference':False,'case_count':len(checks),'passed':sum(c['passed'] for c in checks),'cases':checks}
print(json.dumps(out,indent=2))
if out['passed']!=out['case_count']:raise SystemExit(1)
