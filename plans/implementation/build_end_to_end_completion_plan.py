"""Generate/validate M planning artifacts only; never accept or run product work."""
import csv
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

# ID, title, dependency numbers, inherited FIN/UI/ACL coverage.
ROWS = [
    (1, 'Baseline and requirement reconciliation', [], [1], [], []),
    (2, 'Qualification environments, reviewers and frozen test contracts', [1], [2,20], [], []),
    (3, 'Database identity, ownership, scoped deduplication and enforcement', [1,2], [4,5], [], [1,2,3]),
    (4, 'Complete derived provenance and revocation', [3], [4,9,10,15], [], [5,6]),
    (5, 'Sharing, group and audited admin API/UI', [3,4], [4,19], [], [4]),
    (6, 'Durable authorized ingestion and atomic indexing', [3,4], [10,18], [4], [7]),
    (7, 'Independent private-adapter acceptance', [3,4,5,6], [4,5,20], [], [8]),
    (8, 'Extraction, typed facts and source lineage', [2,6], [8,10,13], [], []),
    (9, 'Knowledge, memory and governed learning', [4,7,8], [9,14,15], [7], []),
    (10, 'Authorized full-library hybrid retrieval', [6,7,8,9], [11], [5], []),
    (11, 'Grounded CPU chat and durable resource accounting', [9,10], [12,17], [6], []),
    (12, 'Exact PDF citations and honest fallback', [7,8], [10,13,19], [2,3], []),
    (13, 'Engineering flows and task continuity', [9,11], [16,17,18], [], []),
    (14, 'Complete real browser workflows and accessibility', [5,7,9,10,11,12,13], [19], [1,7], []),
    (15, 'P0/P1 capacity and upload-envelope qualification', [6,10,11,12,14], [18], [8], []),
    (16, 'Runtime, launchers, migration, backup and recovery', [3,6,7], [3,5,6,7], [], []),
    (17, 'Frozen candidate and integrated adversarial qualification', [14,15,16], [1,3,20], [9], []),
    (18, 'Canonical security and exact-image package acceptance', [2,17], [2,3,20], [], []),
    (19, 'Rights, exact archive and final documentation acceptance', [1,17], [21,23], [], []),
    (20, 'Untouched-subject and independent cold-start acceptance', [17], [24], [9], []),
    (21, 'Independent release acceptance and controlled CPU commissioning', [18,19,20], [22], [10], []),
    (22, 'Evolus/AMD preparation handoff; no partner activation', [21], [23], [], []),
]


def identity(prefix, number):
    return f'{prefix}-{number:02d}'


def main():
    old = json.loads((HERE/'completion-repair-plan.json').read_text(encoding='utf-8'))
    research = json.loads((HERE/'research-workspace-integration-plan.json').read_text(encoding='utf-8'))
    packages = []
    for number, title, dependencies, fin, ui, acl in ROWS:
        packages.append(dict(id=identity('E2E',number), title=title,
            dependencies=[identity('E2E',n) for n in dependencies],
            fin_cards=[identity('FIN',n) for n in fin],
            ui_cards=[identity('UI',n) for n in ui],
            acl_cards=[identity('ACL',n) for n in acl], status='PLANNED',
            implementation_owner='UNASSIGNED', independent_reviewer='UNASSIGNED',
            accepted=False,
            contract='M_END_TO_END_COMPLETION_AND_CERTIFICATION.md#'+
                     f'e2e-{number:02d}--'+title.lower().replace(' ','-'),
            evidence_directory=f'evidence/end-to-end/E2E-{number:02d}/'))
    # Stable links use the actual heading anchor, not title-derived guesses.
    import re
    document = (HERE/'M_END_TO_END_COMPLETION_AND_CERTIFICATION.md').read_text(encoding='utf-8')
    headings = dict(re.findall(r'^### (E2E-\d{2}) — (.+)$', document, re.MULTILINE))
    for package in packages:
        heading = package['id']+' — '+headings[package['id']]
        anchor = re.sub(r'[^\w\- ]', '', heading.lower()).replace(' ', '-')
        package['contract'] = 'M_END_TO_END_COMPLETION_AND_CERTIFICATION.md#'+anchor
    ids = {p['id'] for p in packages}
    errors = []
    if len(ids) != 22 or set(headings) != ids:
        errors.append('Human/machine package inventory mismatch')
    for package in packages:
        for dependency in package['dependencies']:
            if dependency not in ids:
                errors.append(package['id']+': missing dependency '+dependency)
    visiting, visited = set(), set()
    by_id = {p['id']: p for p in packages}
    def visit(name):
        if name in visiting:
            errors.append('Dependency cycle at '+name)
            return
        if name in visited or name not in by_id:
            return
        visiting.add(name)
        for dependency in by_id[name]['dependencies']:
            visit(dependency)
        visiting.remove(name)
        visited.add(name)
    for name in sorted(ids):
        visit(name)
    expected = dict(fin_cards={c['id'] for c in old['cards']},
                    ui_cards={c['id'] for c in research['cards']},
                    acl_cards={identity('ACL',n) for n in range(1,9)})
    for key, inventory in expected.items():
        actual = {c for p in packages for c in p[key]}
        if actual != inventory:
            errors.append(key+': missing or unexpected package mapping')
    def mapped(fin_ids):
        return sorted(p['id'] for p in packages if set(fin_ids) & set(p['fin_cards']))
    original = {c['id']: mapped(c['completion_cards']) for c in old['original_card_coverage']}
    checklist = {c['id']: mapped(c['completion_cards']) for c in old['checklist_coverage']}
    references = {key: mapped(value) for key,value in old['research_coverage'].items()}
    for group in [original,checklist,references]:
        if any(not value for value in group.values()):
            errors.append('Unmapped inherited requirement')
    counts = dict(original_cards=len(original),
                  original_criteria=sum(len(c['criteria']) for c in old['original_card_coverage']),
                  checklist_requirements=len(checklist), research_cards=len(references),
                  fin_packages=len(expected['fin_cards']), ui_packages=len(expected['ui_cards']),
                  acl_packages=len(expected['acl_cards']), execution_packages=len(packages))
    if (counts['original_cards'],counts['original_criteria'],counts['checklist_requirements'],
            counts['research_cards']) != (89,301,209,9):
        errors.append('Inherited authoritative requirement counts changed')
    paths = [HERE/'M_END_TO_END_COMPLETION_AND_CERTIFICATION.md',
             HERE/'build_end_to_end_completion_plan.py', HERE/'completion-repair-plan.json',
             HERE/'research-workspace-integration-plan.json',
             HERE/'L_PRIVATE_DOCUMENT_AUTHORIZATION.md', HERE/'backlog.json',
             HERE/'release-validation-extension.json']
    bindings = {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    report = dict(schema_version='nsai.end-to-end-completion-plan/1', planning_date='2026-10-15',
        scope='Planning only; no implementation, certification or deployment performed',
        certified=False, release_approved=False, partner_rollout_ready=False,
        source_bindings=bindings, packages=packages, original_card_coverage=original,
        checklist_coverage=checklist, research_coverage=references,
        coverage_counts=counts,
        external_prerequisites=['Effective managed filesystem profile for canonical deep scan',
                                'Assigned independent engineering/security/domain reviewers',
                                'Rights-cleared independent fixtures and approved numeric test contracts',
                                'Qualification hardware/storage sufficient for P1 workload'],
        acceptance_rule='All mandatory criteria need fresh exact-artifact evidence and independent review; mapping is not acceptance')
    validation = dict(status='PASS' if not errors else 'FAIL', errors=errors,
                      scope='Planning inventory, inherited coverage and dependency graph only',
                      product_certified=False, coverage_counts=counts)
    (HERE/'end-to-end-completion-plan.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    tracker = HERE/'end-to-end-completion-tracker.csv'
    if tracker.exists():
        with tracker.open(newline='',encoding='utf-8') as stream:
            existing = list(csv.DictReader(stream))
        if len(existing) != len(ids) or {row['id'] for row in existing} != ids:
            validation['status'] = 'FAIL'
            errors.append('Existing execution tracker inventory requires explicit reconciliation')
        # Never reset execution state, owners, reviewer decisions or evidence.
    else:
        with tracker.open('x',newline='',encoding='utf-8') as stream:
            writer = csv.DictWriter(stream,fieldnames=['id','title','dependencies','status',
                'implementation_owner','independent_reviewer','accepted','fin_cards','ui_cards',
                'acl_cards','evidence_directory','evidence_receipt','review_verdict'])
            writer.writeheader()
            for package in packages:
                row = {key:value for key,value in package.items() if key != 'contract'}
                for key in ['dependencies','fin_cards','ui_cards','acl_cards']:
                    row[key] = ';'.join(row[key])
                writer.writerow(row)
    (HERE/'end-to-end-completion-validation.json').write_text(json.dumps(validation,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(validation))
    return 0 if not errors else 1


if __name__ == '__main__':
    raise SystemExit(main())
