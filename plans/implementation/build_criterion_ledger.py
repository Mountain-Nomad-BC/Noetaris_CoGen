"""Expand inherited acceptance obligations; mapping never supplies acceptance."""
import csv
import hashlib
import json
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def main():
    inputs={}
    def read(relative):
        raw=(ROOT/relative).read_bytes()
        inputs[relative]=hashlib.sha256(raw).hexdigest()
        return raw.decode('utf-8')
    plan=json.loads(read('plans/implementation/end-to-end-completion-plan.json'))
    original=json.loads(read('plans/implementation/backlog.json'))
    extension=json.loads(read('plans/implementation/release-validation-extension.json'))
    ui=json.loads(read('plans/implementation/research-workspace-integration-plan.json'))
    research=read('docs/implementation/REFERENCE_RESEARCH_EXTENSION.md')
    acl=read('plans/implementation/L_PRIVATE_DOCUMENT_AUTHORIZATION.md')
    rows=[]
    def add(key,kind,source,requirement,packages):
        if not packages:raise ValueError('Unmapped obligation: '+key)
        rows.append(dict(id=key,kind=kind,source=source,requirement=requirement,
            execution_packages=';'.join(sorted(packages)),implementation_owner='Codex',
            independent_reviewer='UNASSIGNED',implementation_paths='',test_ids='',
            evidence_receipts='',evidence_scope_review='NOT_REVIEWED',
            disposition='NOT_ACCEPTED',review_date='',review_rationale=''))
    for card in original['cards']:
        for number,criterion in enumerate(card['acceptance_criteria'],1):
            add(card['id']+f'.C{number:02d}','original-criterion',
                'plans/implementation/backlog.json#'+card['id'],criterion,
                plan['original_card_coverage'][card['id']])
    for requirement in extension['requirements']:
        add(requirement['id'],'release-checklist',
            'plans/implementation/release-validation-extension.json#'+requirement['id'],
            requirement['requirement'],plan['checklist_coverage'][requirement['id']])
    for line in research.splitlines():
        if not re.match(r'^\| REF-\d{2} \|',line):continue
        cells=[cell.strip() for cell in line.strip('|').split('|')]
        add(cells[0],'research-card','docs/implementation/REFERENCE_RESEARCH_EXTENSION.md#'+cells[0],
            cells[2]+' Acceptance: '+cells[3],plan['research_coverage'][cells[0]])
    for card in ui['cards']:
        packages=[p['id'] for p in plan['packages'] if card['id'] in p['ui_cards']]
        add(card['id'],'ui-card','plans/implementation/research-workspace-integration-plan.json#'+card['id'],
            card['scope_and_acceptance'],packages)
    for line in acl.splitlines():
        if not re.match(r'^\| ACL-\d{2} ',line):continue
        cells=[cell.strip() for cell in line.strip('|').split('|')]
        key=cells[0].split()[0]
        packages=[p['id'] for p in plan['packages'] if key in p['acl_cards']]
        add(key,'authorization-card','plans/implementation/L_PRIVATE_DOCUMENT_AUTHORIZATION.md#'+key,
            cells[1]+' Acceptance: '+cells[2],packages)
    counts={kind:sum(r['kind']==kind for r in rows) for kind in sorted({r['kind'] for r in rows})}
    assert counts=={'original-criterion':301,'release-checklist':209,'research-card':9,'ui-card':10,'authorization-card':8},counts
    assert len({r['id'] for r in rows})==len(rows)
    target=HERE/'criterion-evidence-ledger.csv'
    fields=list(rows[0])
    if target.exists():
        with target.open(encoding='utf-8',newline='') as stream:existing={r['id']:r for r in csv.DictReader(stream)}
        assert set(existing)=={r['id'] for r in rows},'Explicit inventory reconciliation required'
        for row in rows:
            old=existing[row['id']]
            assert all(old[k]==row[k] for k in ('id','kind','source','requirement','execution_packages')),'Explicit requirement reconciliation required'
            for field in fields[5:]:row[field]=old[field]
    with target.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    result=dict(status='PASS_MAPPING_ONLY',product_certified=False,release_approved=False,
        input_sha256=inputs,counts=counts,total_rows=len(rows),
        unassigned_reviewers=sum(r['independent_reviewer']=='UNASSIGNED' for r in rows),
        rows_with_evidence=sum(bool(r['evidence_receipts']) for r in rows),
        ledger_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
        limitation='Complete obligation inventory only; empty implementation/test/evidence assignments remain open. Existing review state is never reset. No criterion is accepted by this generator.')
    (HERE/'criterion-evidence-ledger-validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result))


if __name__=='__main__':main()
