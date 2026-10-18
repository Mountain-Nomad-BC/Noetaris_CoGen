"""Validate appended checklist planning coverage; never execute product or reference code."""
from pathlib import Path
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ledger_path = HERE / 'release-validation-extension.json'
ledger = json.loads(ledger_path.read_text(encoding='utf-8'))
source = Path(ledger['source']['path']).read_bytes()
assert hashlib.sha256(source).hexdigest() == ledger['source']['sha256'], 'Checklist changed'
lines = source.decode('utf-8-sig').splitlines()
expected = set()
section = None
for number, line in enumerate(lines, 1):
    heading = re.match(r'## (\d+)\. ', line)
    if heading:
        section = int(heading[1])
    if line.startswith('- [ ] '):
        expected.add(number)
    if section == 10 and line.startswith('| ') and not line.startswith(('| Scenario', '|---')):
        expected.add(number)
    if section == 14 and line.startswith('| ') and not line.startswith(('| Field', '|---')):
        expected.add(number)
    if section == 17 and re.match(r'\d+\. ', line):
        expected.add(number)
rows = ledger['requirements']
assert {r['source_line'] for r in rows} == expected, 'Missing or unexpected source requirement'
assert len(rows) == len(expected) == len({r['id'] for r in rows}), 'Duplicate requirement'
cards = {c['id']: c for c in ledger['cards']}
assert len(cards) == 18
base = json.loads((HERE / 'backlog.json').read_text(encoding='utf-8'))
base_ids = {c['id'] for c in base['cards']}
assert len(base_ids) == 89
ref_ids = {f'REF-{n:02d}' for n in range(1, 10)}
seen_refs = set()
for row in rows:
    assert row['punch_card'] in cards
    assert row['id'] in cards[row['punch_card']]['requirements']
    assert row['requirement'] and row['owner_role'] and row['reason']
    assert row['disposition'] in ledger['allowed_dispositions']
    assert row['disposition'] != 'PASS', 'No acceptance authorized by planning'
    assert set(row['existing_cards']) <= base_ids
    assert set(row['reference_cards']) <= ref_ids
    seen_refs.update(row['reference_cards'])
assert seen_refs == ref_ids, 'Unallocated research card'
visiting, visited = set(), set()
def visit(card_id):
    assert card_id not in visiting, 'Dependency cycle'
    if card_id in visited:
        return
    visiting.add(card_id)
    for dependency in cards[card_id]['dependencies']:
        assert dependency in cards
        visit(dependency)
    visiting.remove(card_id)
    visited.add(card_id)
for card_id in cards:
    visit(card_id)
assert not ledger['release_approved']
receipt = {
    'status': 'PASS_PLANNING_COVERAGE_ONLY',
    'planning_date': '2026-10-14',
    'checklist_sha256': ledger['source']['sha256'],
    'ledger_sha256': hashlib.sha256(ledger_path.read_bytes()).hexdigest(),
    'source_requirements': len(expected),
    'mapped_requirements': len(rows),
    'work_packages': len(cards),
    'original_cards_preserved': len(base_ids),
    'research_cards_allocated': len(seen_refs),
    'dependencies_acyclic': True,
    'accepted_requirements': 0,
    'production_changed': False,
    'limitations': ['Planning validation only; no product, security or release acceptance.'],
}
destination = ROOT / 'evidence/reference-research/release-checklist-plan-validation.json'
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
print(json.dumps(receipt))
