"""Independent supplemental lineage and corpus-map checks; never promote research."""
import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ingest_arxiv_corpus import private_file
from validate_research_lineage import digest, require, validate_document

ROOT = Path(__file__).resolve().parents[1]


def canonical_digest(value):
    return digest(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode())


def load(folder, entry):
    path = private_file(folder, entry['path'])
    require(path.stat().st_size <= 32*1024*1024, 'Supplement artifact exceeds bound')
    raw = path.read_bytes()
    require(digest(raw) == entry['sha256'], 'Supplement artifact bytes')
    return json.loads(raw)


def validate_inventory(row, kinds, *, author_expected):
    """This full-corpus oracle requires every applicable extraction record, even partial ones."""
    expected = {'author_math'} if author_expected else set()
    if row['pages_requiring_ocr']:
        expected.add('ocr')
    require(len(kinds) == len(set(kinds)) and set(kinds) == expected, 'Expected supplement inventory mismatch')


def validate_supplement(row, supplement, extraction, graph, embeddings, memory, model_identity):
    kind = supplement['kind']
    require(kind in ('ocr', 'author_math'), 'Supplement kind')
    if kind == 'ocr':
        require(extraction['original_sha256'] == row['source_sha256'], 'OCR source binding')
        require(supplement['quality_verified'] is False and supplement['math_recognition_supported'] is False, 'OCR unsupported quality claim')
        require(supplement['processing_complete'] is extraction['complete'], 'OCR completeness claim')
        require(supplement['pages'] == extraction['pages'], 'OCR page coverage payload')
        spans = [dict(s, locator='ocr:'+s['locator']) for s in extraction['spans'] if s.get('extraction') == 'ocr']
        require(len(spans) == supplement['recognized_spans'], 'OCR span count')
        graph_kind = 'ocr_english_uncalibrated'
    else:
        require(extraction['document_id'] == row['document_id'] and extraction['revision'] == row['revision'] and extraction['pdf_sha256'] == row['source_sha256'], 'Author source association')
        require(extraction['authority_granted'] is False and extraction['pdf_alignment'] == 'not_verified' and supplement['pdf_alignment'] == 'not_verified', 'Author authority or alignment')
        require(extraction['source_archive_sha256'] == supplement['source_archive_sha256'], 'Author archive association')
        require(extraction['processing_complete'] is supplement['processing_complete'], 'Author completeness claim')
        require(len(extraction['records']) == supplement['formula_candidates'], 'Author formula count')
        for record in extraction['records']:
            require(record['source_sha256'] == row['source_sha256'] and record['source_archive_sha256'] == extraction['source_archive_sha256'], 'Author record association')
            require(record['document_id'] == row['document_id'] and record['revision'] == row['revision'], 'Author record identity')
            require(record['evaluation'] == 'not_attempted' and record['generated_execution'] is False and record['pdf_alignment'] == 'not_verified', 'Author execution or alignment claim')
            require(record['source']['page'] is None and record['source']['text'] == record['latex'], 'Author quote or false page alignment')
        spans = [dict(locator='author-tex:'+r['id'], text=r['latex']) for r in extraction['records']]
        graph_kind = 'author_tex_math_not_pdf_aligned'
    if not spans:
        require(graph is None and embeddings is None and memory is None, 'Empty extraction cannot have graph artifacts')
        return dict(kind=kind, graph_available=False, extraction_complete=supplement['processing_complete'])
    require(graph is not None and embeddings is not None and memory is not None, 'Missing supplement graph artifacts')
    require(graph['extraction_kind'] == graph_kind, 'Supplement graph kind')
    require(graph['extraction_evidence_sha256'] == canonical_digest(extraction), 'Supplement extraction content binding')
    formulas = dict(document_id=row['document_id'], revision=row['revision'], original_sha256=row['source_sha256'], records=[])
    result = validate_document(dict(original_sha256=row['source_sha256'], spans=spans), graph, formulas, embeddings, memory,
                               document_id=row['document_id'], revision=row['revision'], original_sha256=row['source_sha256'], model_identity=model_identity)
    return dict(kind=kind, graph_available=True, extraction_complete=supplement['processing_complete'], **result)


def validate_map(manifest, mapping, semantics, document_vectors):
    expected = {r['document_id']:r for r in manifest['papers']}
    require(mapping['authority_granted'] is False, 'Map authority')
    require(mapping['model_identity'] == semantics['model_identity'] == manifest['semantic_model'], 'Map model identity')
    nodes = {n['id']:n for n in mapping['nodes']}
    require(len(nodes) == len(mapping['nodes']) and set(nodes) == set(expected) == set(semantics['vectors']), 'Map document bijection')
    for identity, node in nodes.items():
        require(node['source_sha256'] == expected[identity]['source_sha256'], 'Map source digest')
        vector = semantics['vectors'][identity]
        source_vectors, coverage = document_vectors[identity]
        require(len(vector) == 384 and all(type(v) in (int,float) and math.isfinite(v) for v in vector), 'Map vector shape')
        weighted = [math.fsum(values[d]*coverage[key]['input_tokens'] for key, values in source_vectors.items()) for d in range(384)]
        norm = math.sqrt(math.fsum(v*v for v in weighted))
        require(norm > 0 and all(abs(a-b/norm) < 1e-10 for a,b in zip(vector,weighted)), 'Map centroid derivation')
    pairs = {(e['source_id'],e['target_id']) for e in mapping['edges']}
    require(len(pairs) == len(mapping['edges']), 'Duplicate map edge')
    for edge in mapping['edges']:
        left, right = edge['source_id'], edge['target_id']
        require(left in nodes and right in nodes and left != right, 'Map dangling or self edge')
        require(edge['authority_granted'] is False and edge['entailment_verified'] is False and edge['kind'] == 'semantic_neighbour_candidate', 'Map factual authority claim')
        require(edge['model_sha256'] == manifest['semantic_model']['sha256'], 'Map edge model')
        cosine = math.fsum(a*b for a,b in zip(semantics['vectors'][left], semantics['vectors'][right]))
        require(type(edge['cosine']) in (int,float) and math.isfinite(edge['cosine']) and abs(edge['cosine']-cosine) < 1e-10, 'Map cosine mismatch')
    for left, vector in semantics['vectors'].items():
        ranked = sorted(((math.fsum(a*b for a,b in zip(vector,other)),right) for right,other in semantics['vectors'].items() if left != right), reverse=True)
        require({right for a,right in pairs if a==left} == {right for _,right in ranked[:3]}, 'Map nearest neighbours')
    return dict(documents=len(nodes), edges=len(pairs))


def run(manifest_path, enrichment_path):
    raw = manifest_path.read_bytes()
    manifest = json.loads(raw)
    enrichment_raw = enrichment_path.read_bytes()
    enrichment = json.loads(enrichment_raw)
    require(enrichment['prepared_manifest_sha256'] == digest(raw), 'Supplement generation binding')
    require(enrichment['model_identity'] == manifest['semantic_model'], 'Supplement model binding')
    author_binding = enrichment.get('author_source_manifest_sha256')
    require(isinstance(author_binding,str) and len(author_binding)==64 and all(c in '0123456789abcdef' for c in author_binding), 'Full supplement qualification requires author source manifest binding')
    indexed = {p['document_id']:p for p in manifest['papers']}
    require(len(enrichment['papers']) == len(indexed) and {p['document_id'] for p in enrichment['papers']} == set(indexed), 'Supplement document bijection')
    report = dict(status='PASS_STRUCTURAL_ONLY', captured_at=datetime.now(timezone.utc).isoformat(), prepared_manifest_sha256=digest(raw),
                  enrichment_manifest_sha256=digest(enrichment_raw), supplements=[], release_approved=False,
                  limitations=['Archive quote bytes require the separate author-source custody receipt.', 'OCR character accuracy and mathematical/scientific correctness remain unqualified.', 'Two rotated pages and one unavailable TeX source remain explicit gaps.'])
    for document in enrichment['papers']:
        row = indexed[document['document_id']]
        require(document['source_sha256'] == row['source_sha256'], 'Supplement source identity')
        kinds = [s['kind'] for s in document['supplements']]
        validate_inventory(row,kinds,author_expected=True)
        for supplement in document['supplements']:
            folder = private_file(enrichment_path.parent, row['document_id']+'/'+supplement['folder']+'/'+supplement['extraction']['path']).parent
            extraction = load(folder, supplement['extraction'])
            files = supplement['files']
            graph, embeddings, memory = (load(folder, files[key]) for key in ('knowledge','embeddings','memory')) if files else (None,None,None)
            result = validate_supplement(row, supplement, extraction, graph, embeddings, memory, manifest['semantic_model'])
            report['supplements'].append(dict(document_id=row['document_id'], **result))
    document_vectors = {}
    for row in manifest['papers']:
        payload = load(manifest_path.parent/row['document_id'], row['files']['embeddings'])
        document_vectors[row['document_id']] = (payload['vectors'], payload['coverage'])
    report['corpus_map'] = validate_map(manifest, load(manifest_path.parent,manifest['corpus_map']), load(manifest_path.parent,manifest['document_semantics']), document_vectors)
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--enrichment-manifest',type=Path,required=True)
    args = p.parse_args()
    destination = ROOT/'evidence/release-validation/REF-07'/uuid4().hex
    destination.mkdir(parents=True,exist_ok=False)
    try:
        report = run(args.manifest.resolve(), args.enrichment_manifest.resolve())
    except Exception as error:
        report = dict(status='FAIL',error_type=type(error).__name__,release_approved=False)
        (destination/'supplement-lineage.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        raise
    (destination/'supplement-lineage.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=report['status'], supplements=len(report['supplements']), corpus_map=report['corpus_map'], receipt=str(destination.relative_to(ROOT)))))


if __name__ == '__main__':
    main()
