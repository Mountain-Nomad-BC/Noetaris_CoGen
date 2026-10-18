"""Compare candidate capability declarations with static routes and scoped evidence."""
import ast
import hashlib
import json
from pathlib import Path
import re
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from nsai.capabilities import registry


def normalized(route):
    return re.sub(r'\{[^{}]+\}', '{}', route)


def main():
    api = ROOT / 'src/nsai/api.py'
    raw = api.read_bytes()
    tree = ast.parse(raw)
    routes = []
    for function in ast.walk(tree):
        if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in function.decorator_list:
            if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute) or not decorator.args:
                continue
            if not isinstance(decorator.func.value, ast.Name) or decorator.func.value.id != 'app':
                continue
            if decorator.func.attr not in {'get','head','post','put','delete','patch','api_route'}:
                continue
            if not isinstance(decorator.args[0], ast.Constant) or not isinstance(decorator.args[0].value, str):
                continue
            routes.append(dict(path=decorator.args[0].value, decorator=decorator.func.attr,
                               handler=function.name, file='src/nsai/api.py', line=function.lineno))
    tests = []
    for path in sorted((ROOT / 'tests').glob('test_*.py')):
        raw_test = path.read_bytes()
        tests.append((path.relative_to(ROOT).as_posix(), raw_test.decode('utf-8'), hashlib.sha256(raw_test).hexdigest()))
    rows = []
    for capability in registry(ocr_configured=False):
        matching = [r for r in routes if any(normalized(r['path']) == normalized(p) for p in capability['routes'])]
        references = [dict(path=p, sha256=h) for p, text, h in tests if any(normalized(route) in normalized(text) for route in capability['routes'])]
        rows.append(dict(id=capability['id'], advertised='candidate registry only; live capabilities not inferred',
                         declared_state=capability['state'], declared_routes=capability['routes'],
                         executable_route_declarations=matching,
                         integration_verdict='DECLARATION_ONLY_REQUIRES_RUNTIME_REVIEW',
                         test_source_mentions=references,
                         test_verdict='SOURCE_MENTIONS_ARE_NOT_EXECUTION_EVIDENCE',
                         demonstrated='NOT_INDEPENDENTLY_ADMITTED', limitations=capability['limitations'],
                         permissions=capability['permissions'], release_approved=False))
    evidence = json.loads((ROOT / 'evidence/release-validation/current.json').read_bytes())
    report = dict(status='STATIC_CLAIM_MATRIX_ONLY', api_sha256=hashlib.sha256(raw).hexdigest(),
                  capabilities=rows, observed_route_declarations=routes,
                  candidate_evidence_catalog='evidence/release-validation/current.json', candidate_image=evidence['api_candidate'],
                  warning='Existing receipts require per-claim, exact-build review; no demonstrated or tested field is inferred from code or counts.',
                  release_approved=False)
    destination = ROOT / 'evidence/release-validation/REL-C00' / uuid4().hex
    destination.mkdir(parents=True, exist_ok=False)
    (destination / 'capability-matrix.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(status=report['status'], capabilities=len(rows), route_declarations=len(routes), receipt=destination.relative_to(ROOT).as_posix()+'/capability-matrix.json')))


if __name__ == '__main__':
    main()
