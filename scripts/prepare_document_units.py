"""Persist a separate private document-unit generation with bounded local CPU measurements."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys
import time
import tracemalloc
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from nsai.document_units import assemble_document_units
from ingest_arxiv_corpus import private_file, write


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,required=True)
    args=p.parse_args()
    raw=args.manifest.read_bytes()
    if len(raw)>8*1024*1024:raise ValueError('Manifest exceeds bound')
    manifest=json.loads(raw)
    if not 1<=len(manifest['papers'])<=100:raise ValueError('Document inventory exceeds bound')
    run_id='document-units-'+uuid4().hex[:12]
    destination=ROOT/'data/arxiv-corpus'/run_id
    destination.mkdir(exist_ok=False)
    source=ROOT/'src/nsai/document_units.py'
    before=source.read_bytes()
    report=dict(run_id=run_id,status='RUNNING',prepared_manifest_sha256=hashlib.sha256(raw).hexdigest(),
        source_sha256=hashlib.sha256(before).hexdigest(),producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        captured_at=datetime.now(timezone.utc).isoformat(),documents=[],release_approved=False,
        benchmark_scope='Host CPU pure projection, 30 repeated warm samples/document plus first call; no service throughput or OCR quality claim.')
    try:
        for row in manifest['papers']:
            path=private_file(args.manifest.parent/row['document_id'],row['files']['parsed']['path'])
            if path.stat().st_size>32*1024*1024:raise ValueError('Parsed artifact exceeds bound')
            parsed_raw=path.read_bytes()
            if hashlib.sha256(parsed_raw).hexdigest()!=row['files']['parsed']['sha256']:raise ValueError('Parsed source integrity')
            parsed=json.loads(parsed_raw)
            if parsed['original_sha256']!=row['source_sha256']:raise ValueError('Original source association')
            def project():return assemble_document_units(row['document_id'],row['revision'],row['source_sha256'],parsed['spans'])
            started=time.perf_counter();projection=project();first=time.perf_counter()-started
            samples=[]
            for _ in range(30):
                started=time.perf_counter();candidate=project();samples.append(time.perf_counter()-started)
                if candidate!=projection:raise ValueError('Nondeterministic projection')
            if [(u['locator'],u['text']) for u in projection['units']]!=[(s['locator'],s['text']) for s in parsed['spans']]:
                raise ValueError('Unit source coverage mismatch')
            tracemalloc.start()
            try:
                project();_,peak=tracemalloc.get_traced_memory()
            finally:tracemalloc.stop()
            entry=write(destination/(row['document_id']+'.json'),projection)
            report['documents'].append(dict(document_id=row['document_id'],file=entry,units=len(projection['units']),
                first_call_seconds=first,warm_seconds=samples,warm_median_seconds=sorted(samples)[15],
                warm_p95_sample_seconds=sorted(samples)[math.ceil(.95*len(samples))-1],
                traced_python_peak_bytes=peak,source_exact=True,authority_granted=False))
        if source.read_bytes()!=before or args.manifest.read_bytes()!=raw:raise ValueError('Source changed during preparation')
        report['status']='PASS_PROJECTION_ONLY'
    except Exception as error:
        report['status']='FAIL';report['error_type']=type(error).__name__
        raise
    finally:
        write(destination/'manifest.json',report)
        write(ROOT/'evidence/release-validation'/(run_id+'.json'),report)
    print(json.dumps(dict(status=report['status'],documents=len(report['documents']),manifest=str((destination/'manifest.json').relative_to(ROOT)))))


if __name__=='__main__':
    main()
