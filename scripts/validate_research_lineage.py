"""Independent structural oracle for native research artifacts, not a scientific truth test."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ingest_arxiv_corpus import private_file


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def validate_document(parsed, graph, formulas, embeddings, memory, *, document_id, revision, original_sha256, model_identity):
    source = dict(document_id=document_id, revision=revision, source_sha256=original_sha256)
    require(parsed['original_sha256'] == original_sha256, 'Original digest association')
    require(graph['source'] == source and memory['source'] == source, 'Source identity')
    require(graph['authority_granted'] is False and graph['state'] == 'candidate', 'Candidate authority')
    require(graph['source_processing_complete'] is True and graph['omissions'] == 0, 'Incomplete graph')
    raw = json.dumps({k:v for k,v in graph.items() if k != 'graph_sha256'}, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode()
    require(digest(raw) == graph['graph_sha256'], 'Graph content digest')
    spans = {s['locator']:s for s in parsed['spans']}
    require(len(spans) == len(parsed['spans']), 'Duplicate source locator')
    nodes = {n['id']:n for n in graph['nodes']}
    require(len(nodes) == len(graph['nodes']), 'Duplicate graph node')
    require(len({e['id'] for e in graph['edges']}) == len(graph['edges']), 'Duplicate graph edge')
    for edge in graph['edges']:
        require(edge['source_id'] in nodes and edge['target_id'] in nodes, 'Dangling edge')
        require(edge['provenance'] == source and edge['authority_granted'] is False, 'Edge provenance or authority')
    passages = set()
    source_nodes = set()
    passage_intervals = {locator: [] for locator in spans}
    for node in nodes.values():
        require(node['source'] == source and node['authority_granted'] is False, 'Node provenance or authority')
        kind = node['kind']
        if kind in ('source_span', 'observation', 'passage', 'formula'):
            require(node['locator'] in spans, 'Unanchored native node')
        if kind == 'source_span':
            require(node['text'] == spans[node['locator']]['text'], 'Source span text mismatch')
            source_nodes.add(node['locator'])
        if kind == 'observation':
            start, end = node['char_start'], node['char_end']
            text = spans[node['locator']]['text']
            require(type(start) is int and type(end) is int and 0 <= start < end <= len(text), 'Observation bounds')
            require(node['text'] == text[start:end], 'Observation quote mismatch')
        if kind == 'passage':
            passages.add(node['id'])
            parts = []
            for segment in node['source_segments']:
                require(segment['locator'] in spans, 'Passage locator')
                text = spans[segment['locator']]['text']
                start, end = segment['char_start'], segment['char_end']
                require(type(start) is int and type(end) is int and 0 <= start < end <= len(text), 'Passage bounds')
                require(segment['text'] == text[start:end], 'Passage quote mismatch')
                passage_intervals[segment['locator']].append((start, end))
                parts.append(segment['text'])
            require(node['text'] == '\n'.join(parts), 'Passage assembly mismatch')
    require(source_nodes == set(spans), 'Missing source span node')
    for locator, intervals in passage_intervals.items():
        cursor = 0
        for start, end in sorted(intervals):
            require(start <= cursor, 'Passage source coverage gap')
            cursor = max(cursor, end)
        require(cursor == len(spans[locator]['text']), 'Passage source coverage incomplete')
    require(formulas['document_id'] == document_id and formulas['revision'] == revision and formulas['original_sha256'] == original_sha256, 'Formula document binding')
    formula_ids = set()
    for formula in formulas['records']:
        require(formula['id'] not in formula_ids, 'Duplicate formula')
        formula_ids.add(formula['id'])
        require(formula['document_id'] == document_id and formula['revision'] == revision and formula['source_sha256'] == original_sha256, 'Formula source binding')
        quote = formula['source']
        require(quote['locator'] in spans, 'Formula locator')
        span = spans[quote['locator']]
        require(digest(span['text'].encode()) == quote['span_sha256'], 'Formula span digest')
        start, end = quote['offset_start'], quote['offset_end']
        require(type(start) is int and type(end) is int and 0 <= start < end <= len(span['text']), 'Formula bounds')
        require(quote['text'] == span['text'][start:end] and quote['page'] == span['page'], 'Formula quote or page mismatch')
    graph_formulas = [n['formula_data'] for n in nodes.values() if n['kind'] == 'formula']
    require({f['id'] for f in graph_formulas} == formula_ids and len(graph_formulas) == len(formula_ids), 'Formula graph membership')
    require(all(f in formulas['records'] for f in graph_formulas), 'Formula graph payload')
    require(embeddings['model_identity'] == model_identity, 'Embedding model identity')
    require(set(embeddings['vectors']) == passages == set(embeddings['coverage']), 'Embedding passage bijection')
    for identity in passages:
        vector = embeddings['vectors'][identity]
        require(len(vector) == 384 and all(type(v) in (int, float) and math.isfinite(v) for v in vector), 'Invalid vector')
        require(sum(v*v for v in vector) > 0, 'Zero vector')
        receipt = embeddings['coverage'][identity]
        require(type(receipt['input_tokens']) is int and receipt['input_tokens'] > 0 and receipt['input_tokens'] == receipt['covered_tokens'] and receipt['complete'] is True, 'Token coverage')
    require(memory['canon'] == [] and memory['authority_granted'] is False, 'Memory authority')
    require(all(item['id'] in nodes and item == nodes[item['id']] for item in memory['evidence']), 'Memory graph membership')
    return dict(nodes=len(nodes), edges=len(graph['edges']), formulas=len(formula_ids), passages=len(passages))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    args = parser.parse_args()
    manifest_bytes = args.manifest.read_bytes()
    manifest = json.loads(manifest_bytes)
    report = dict(status='PASS_STRUCTURAL_ONLY', manifest_sha256=digest(manifest_bytes), documents=[], release_approved=False,
                  limitations=['Native graph only; supplement namespaces require separate oracles.', 'No OCR, formula correctness, factual support, graph completeness or semantic relevance certification.'])
    for row in manifest['papers']:
        folder = args.manifest.parent / row['document_id']
        artifacts = {}
        for key, entry in row['files'].items():
            path = private_file(folder, entry['path'])
            require(path.stat().st_size <= 32*1024*1024, 'Artifact exceeds bound')
            raw = path.read_bytes()
            require(digest(raw) == entry['sha256'], 'Artifact byte digest mismatch')
            if key != 'original':
                artifacts[key] = json.loads(raw)
            else:
                require(digest(raw) == row['source_sha256'], 'Original byte digest mismatch')
        artifacts['graph'] = artifacts.pop('knowledge')
        result = validate_document(**artifacts, document_id=row['document_id'], revision=row['revision'], original_sha256=row['source_sha256'], model_identity=manifest['semantic_model'])
        report['documents'].append(dict(document_id=row['document_id'], **result))
    destination = ROOT / 'evidence/release-validation/REF-07' / uuid4().hex
    destination.mkdir(parents=True, exist_ok=False)
    (destination / 'lineage.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(status=report['status'], documents=len(report['documents']), receipt=destination.relative_to(ROOT).as_posix()+'/lineage.json')))


if __name__ == '__main__':
    main()
