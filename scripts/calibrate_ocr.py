"""Original synthetic OCR corpus generation and frozen holdout qualification.

Run on host with --output DIR; it starts only an owned network-none OCR container.
Internal mode uses actual fixed OCR subprocesses, never a mock or provider.
"""
from __future__ import annotations
import argparse
import base64
from collections import Counter
from io import BytesIO
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading
import time

IMAGE='nsai-ocr-qualification:local'
COHORTS=('clean','critical','degraded_table','unsupported_formula')

def labels(document,page):
    number=40+document
    if page==1:
        return dict(cohort='clean',reference=f'Assembly record {document:03d}\nPump maximum temperature is {number} C.\nInspect the inlet before starting.',critical=[str(number),'C','before'])
    if page==2:
        return dict(cohort='critical',reference=f'Revision {document:03d}\nDo not exceed {number}.0 C.\nMinimum is -5 C. Clearance is 0.5 mm.',critical=['not',f'{number}.0','C','-5','0.5','mm'])
    if page==3:
        return dict(cohort='degraded_table',reference=f'Service table {document:03d}\nItem Limit Unit\nInlet {number} C\nGap 0.5 mm',critical=[str(number),'C','0.5','mm'])
    return dict(cohort='unsupported_formula',reference=f'Formula worksheet {document:03d}\nP = V * I\nx = (a + b) / 2\nDo not treat OCR as verified mathematics.',critical=[],supported=False)

def _native_page(label):
    from pypdf import PdfWriter
    from pypdf.generic import DictionaryObject,NameObject,DecodedStreamObject
    writer=PdfWriter();page=writer.add_blank_page(width=612,height=792)
    font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
    page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):writer._add_object(font)})})
    commands=[]
    for index,line in enumerate(label['reference'].split('\n')):
        escaped=line.replace('\\','\\\\').replace('(','\\(').replace(')','\\)')
        commands.append(f'BT /F1 18 Tf 60 {720-index*42} Td ({escaped}) Tj ET')
    if label['cohort']=='degraded_table':
        commands.extend(['0.5 w 55 668 m 555 668 l S','55 582 m 555 582 l S','55 540 m 555 540 l S'])
    stream=DecodedStreamObject();stream.set_data('\n'.join(commands).encode('ascii'))
    page[NameObject('/Contents')]=writer._add_object(stream)
    output=BytesIO();writer.write(output);return output.getvalue()

def raster_page(label,directory,index):
    from pypdf import PdfWriter
    from pypdf.generic import DictionaryObject,NameObject,DecodedStreamObject,NumberObject
    source=directory/f'native-{index}.pdf';source.write_bytes(_native_page(label))
    prefix=directory/f'raster-{index}'
    dpi=65 if label['cohort']=='degraded_table' else 150
    subprocess.run(['pdftoppm','-singlefile','-gray','-r',str(dpi),str(source),str(prefix)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True,timeout=10)
    pgm=prefix.with_suffix('.pgm').read_bytes();header,data=pgm.split(b'\n255\n',1)
    source.unlink()
    prefix.with_suffix('.pgm').unlink()
    lines=[line for line in header.splitlines()[1:] if not line.startswith(b'#')]
    width,height=map(int,b' '.join(lines).split())
    if label['cohort']=='degraded_table':
        mutable=bytearray(data)
        # Deterministic low-contrast scan and sparse sensor artifacts, defined
        # before observing any OCR output. No tune-to-holdout feedback loop.
        for pixel in range(len(mutable)):
            mutable[pixel]=100+mutable[pixel]*140//255
        for pixel in range(index%101,len(mutable),997):mutable[pixel]=160
        data=bytes(mutable)
    writer=PdfWriter();page=writer.add_blank_page(width=612,height=792)
    image=DecodedStreamObject();image.set_data(data)
    image.update({NameObject('/Type'):NameObject('/XObject'),NameObject('/Subtype'):NameObject('/Image'),NameObject('/Width'):NumberObject(width),NameObject('/Height'):NumberObject(height),NameObject('/ColorSpace'):NameObject('/DeviceGray'),NameObject('/BitsPerComponent'):NumberObject(8)})
    page[NameObject('/Resources')]=DictionaryObject({NameObject('/XObject'):DictionaryObject({NameObject('/Im1'):writer._add_object(image.flate_encode())})})
    stream=DecodedStreamObject();stream.set_data(b'q 612 0 0 792 0 0 cm /Im1 Do Q')
    page[NameObject('/Contents')]=writer._add_object(stream)
    output=BytesIO();writer.write(output);return output.getvalue()

def process_memory(pid):
    pending=[pid];seen=set();rss=0;largest=0
    while pending:
        current=pending.pop()
        if current in seen:continue
        seen.add(current)
        try:
            text=Path(f'/proc/{current}/status').read_text()
            match=re.search(r'^VmRSS:\s+(\d+) kB',text,re.MULTILINE)
            value=int(match.group(1))*1024 if match else 0
            rss+=value;largest=max(largest,value)
            pending.extend(map(int,Path(f'/proc/{current}/task/{current}/children').read_text().split()))
        except (OSError,ValueError):pass
    return rss,largest

def run_page(data):
    payload=json.dumps(dict(filename='original.pdf',data=base64.b64encode(data).decode(),language='eng')).encode()
    with tempfile.TemporaryFile() as stdout,tempfile.TemporaryFile() as stderr:
        started=time.monotonic()
        process=subprocess.Popen([sys.executable,'-m','nsai.ocr_worker'],stdin=subprocess.PIPE,stdout=stdout,stderr=stderr,start_new_session=True)
        peak=[0,0];stop=threading.Event()
        def monitor():
            while not stop.wait(.02):
                aggregate,largest=process_memory(process.pid)
                peak[0]=max(peak[0],aggregate);peak[1]=max(peak[1],largest)
        thread=threading.Thread(target=monitor,daemon=True);thread.start()
        try:
            process.communicate(payload,timeout=125)
        except subprocess.TimeoutExpired:
            import signal
            os.killpg(process.pid,signal.SIGKILL);process.wait()
        finally:stop.set();thread.join()
        elapsed=time.monotonic()-started
        stdout.seek(0);stderr.seek(0)
        if process.returncode:
            return dict(error='fixed worker refused',diagnostic=stderr.read(65536).decode(errors='replace'),exit_code=process.returncode,seconds=elapsed,peak_aggregate_rss_bytes=peak[0],peak_process_rss_bytes=peak[1])
        result=json.loads(stdout.read(16*1024*1024+1))
        return dict(result=result,exit_code=process.returncode,seconds=elapsed,peak_aggregate_rss_bytes=peak[0],peak_process_rss_bytes=peak[1])

def evaluate_record(label,run):
    from nsai.ocr_quality import error_rates
    result=run.get('result',{});observed=result.get('raw_text','')
    expected=label['reference']
    # Match critical lexemes as an ordered multiset, retaining signs/decimals;
    # engine output cannot repair or silently normalize critical values.
    expected_tokens=Counter(label['critical'])
    observed_tokens=Counter(re.findall(r'-?\d+(?:\.\d+)?|[A-Za-z]+',observed))
    exact=sum(min(count,observed_tokens[token]) for token,count in expected_tokens.items())
    total=sum(expected_tokens.values())
    words=result.get('ocr_words',[])
    geometry_checks=[]
    for word in words:
        if word.get('pdf_box') and word.get('pixel_box'):
            box=word['pixel_box'];pdf=word['pdf_box']
            reconstructed=[pdf[0]*300/72,(792-pdf[3])*300/72,pdf[2]*300/72,(792-pdf[1])*300/72]
            geometry_checks.append(max(abs(a-b)*72/300 for a,b in zip(box,reconstructed)))
    return dict(raw=error_rates(expected,observed),normalized=error_rates(expected,observed,normalized=True),
        critical_exact=exact,critical_total=total,critical_exact_rate=exact/total if total else None,
        observed=observed,processing_complete=bool(result.get('complete')),supported=label.get('supported',True),
        word_count=len(words),score_probability_claim=any(w.get('engine_score_is_probability') for w in words),
        geometry_roundtrip_max_pt=max(geometry_checks) if geometry_checks else None,
        geometry_scope='transform algebra roundtrip only; no independently labeled glyph boxes/IoU truth')

def summarize(records):
    from nsai.ocr_quality import aggregate_error_rates,percentile
    groups={}
    for split in ('development','holdout'):
        for cohort in COHORTS:
            selected=[record for record in records if record['split']==split and record['cohort']==cohort]
            critical=sum(r['critical_total'] for r in selected)
            raw=aggregate_error_rates([r['raw'] for r in selected]);normalized=aggregate_error_rates([r['normalized'] for r in selected])
            ratio=sum(r['critical_exact'] for r in selected)/critical if critical else None
            clean_gate=(cohort=='clean' and raw['cer'] is not None and raw['cer']<=.01 and raw['wer']<=.03
                and percentile([r['raw']['cer'] for r in selected],95)<=.03 and ratio is not None and ratio>=.995
                and all(r['processing_complete'] and not r.get('error') for r in selected))
            groups[f'{split}/{cohort}']=dict(raw=raw,normalized=normalized,critical_exact_rate=ratio,critical_tokens=critical,
                processing_failures=sum(not r['processing_complete'] for r in selected),
                page_raw_cer_p95=percentile([r['raw']['cer'] for r in selected],95),
                critical_99_5_percent_observed=ratio>=.995 if ratio is not None else None,
                seconds_p50=percentile([r['seconds'] for r in selected],50),seconds_p95=percentile([r['seconds'] for r in selected],95),
                rss_aggregate_p95_bytes=percentile([r['peak_aggregate_rss_bytes'] for r in selected],95),
                rss_process_p95_bytes=percentile([r['peak_process_rss_bytes'] for r in selected],95),
                synthetic_clean_candidate_gate_pass=clean_gate,admission='synthetic-clean candidate proposal only' if clean_gate else 'withheld',
                geometry_iou=None,geometry_iou_reason='No independently labeled glyph boxes in corpus',
                p95_geometry_roundtrip_pt=percentile([r['geometry_roundtrip_max_pt'] for r in selected if r['geometry_roundtrip_max_pt'] is not None],95))
    return groups

def blank_control(output):
    label=dict(cohort='blank',reference='',critical=[],supported=False)
    with tempfile.TemporaryDirectory() as folder:
        data=raster_page(label,Path(folder),9999)
        run=run_page(data)
    receipt=dict(**evaluate_record(label,run),**{key:value for key,value in run.items() if key!='result'},
        fixture='Actual empty raster image embedded in a PDF; recognizer invoked; zero text expected',
        input_sha256=hashlib.sha256(data).hexdigest())
    (output/'blank-raster-control.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(json.dumps(dict(event='blank_control',false_positive=receipt['raw']['empty_reference_false_positive'],exit_code=receipt['exit_code'])),flush=True)

def replay_inputs(output):
    """Reconstruct exact job bytes against frozen hashes without rerunning OCR."""
    manifest=json.loads((output/'frozen-manifest.json').read_text())
    inputs=output/'inputs';inputs.mkdir(exist_ok=True)
    verified=0
    with tempfile.TemporaryDirectory() as folder:
        for index,label in enumerate(manifest):
            data=raster_page(label,Path(folder),index+1)
            # Noise seed is defined by document*4+page, equal index+1.
            digest=hashlib.sha256(data).hexdigest()
            if digest!=label['input_sha256']:
                raise ValueError('Replay input differs from frozen byte identity')
            (inputs/f'{index:03d}.pdf').write_bytes(data);verified+=1
    (output/'input-replay.json').write_text(json.dumps(dict(exact_inputs_verified=verified,engine_reinvoked=False,
        method='same pinned image re-renders independently authored fixed references with frozen deterministic noise seed; each exact SHA256 matched before storage'),indent=2),encoding='utf-8')
    print(json.dumps(dict(event='inputs_replayed',exact_sha256_matches=verified)),flush=True)

def inside(output):
    from pypdf import PdfReader,PdfWriter
    output.mkdir(parents=True,exist_ok=True);corpus=output/'corpus';corpus.mkdir(exist_ok=True)
    manifest=[];page_bytes={}
    with tempfile.TemporaryDirectory() as folder:
        directory=Path(folder)
        for document in range(50):
            writer=PdfWriter();entries=[]
            for page in range(1,5):
                label=labels(document,page);data=raster_page(label,directory,document*4+page)
                inputs=output/'inputs';inputs.mkdir(exist_ok=True);(inputs/f'{document*4+page-1:03d}.pdf').write_bytes(data)
                writer.add_page(PdfReader(BytesIO(data)).pages[0])
                label.update(document_id=f'synthetic-family-{document:03d}',page=page,
                    split='development' if document%5==0 else 'holdout',input_sha256=hashlib.sha256(data).hexdigest())
                entries.append(label);page_bytes[(document,page)]=data
            stream=BytesIO();writer.write(stream);original=stream.getvalue()
            (corpus/f'family-{document:03d}.pdf').write_bytes(original)
            for label in entries:label['original_document_sha256']=hashlib.sha256(original).hexdigest();manifest.append(label)
        # Freeze every reference/input and split before executing any OCR.
        encoded=json.dumps(manifest,sort_keys=True,indent=2).encode()
        (output/'frozen-manifest.json').write_bytes(encoded)
        freeze_hash=hashlib.sha256(encoded).hexdigest()
        print(json.dumps(dict(event='corpus_frozen',documents=50,pages=200,manifest_sha256=freeze_hash)),flush=True)
        records=[]
        for index,label in enumerate(manifest):
            document=int(label['document_id'].split('-')[-1]);run=run_page(page_bytes[(document,label['page'])])
            record=dict(label,**{key:value for key,value in run.items() if key!='result'},**evaluate_record(label,run))
            records.append(record)
            (output/'records.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
            if (index+1)%20==0:print(json.dumps(dict(event='progress',pages_completed=index+1,failures=sum(not r['processing_complete'] for r in records))),flush=True)
        # A blank page is a separate false-positive control, excluded from 200 text pages.
        blank_control(output)
        blank_receipt=json.loads((output/'blank-raster-control.json').read_text())
        groups=summarize(records)
        summary=dict(documents=50,pages=200,development_documents=10,holdout_documents=40,
            manifest_sha256=freeze_hash,groups=groups,blank_control=blank_receipt,
            candidate_admission='Only exact scoped synthetic clean subgroup if its frozen holdout gate passes; all OCR still unverified source/proposal',
            general_domain_qualification=False,formula_recognition_supported=False,geometry_iou_qualified=False,
            memory_measurement='20ms /proc sampled worker+descendant aggregate RSS (shared pages may double-count); sampled lower bound, not kernel peak',
            performance_scope='200 independent single-page projection jobs from50 four-page originals, oneCPU768MiB; not whole-document concurrentSLO',
            limitations=['synthetic Helvetica English only, no real-domain holdout','fixed common grammar may overlap across synthetic families','no labeled glyph boxes/IoU; algebra roundtrip only','handwriting/formulas/languages/complex geometry unsupported','no regression-driven tuning performed after corpus freeze'])
        (output/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
        print(json.dumps(dict(event='complete',pages=200,holdout_clean_gate=groups['holdout/clean']['synthetic_clean_candidate_gate_pass'])),flush=True)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--inside',action='store_true');parser.add_argument('--blank-only',action='store_true');parser.add_argument('--replay-inputs-only',action='store_true');args=parser.parse_args()
    if args.inside:
        if args.replay_inputs_only:replay_inputs(args.output)
        elif args.blank_only:blank_control(args.output)
        else:inside(args.output)
        return
    args.output.mkdir(parents=True,exist_ok=True)
    root=Path(__file__).resolve().parents[1]
    command=['docker','run','--rm','--name','nsai-ocr-cal-'+str(os.getpid()),'--label','nsai.scope=owned-ocr-calibration',
        '--network','none','--read-only','--user','10002:10002','--cap-drop','ALL','--security-opt','no-new-privileges:true',
        '--cpus','1','--memory','768m','--pids-limit','64','--tmpfs','/tmp:rw,noexec,nosuid,size=128m',
        '--mount',f'type=bind,source={Path(__file__).resolve()},target=/calibrate.py,readonly',
        '--mount',f'type=bind,source={root / "src/nsai/ocr_quality.py"},target=/opt/app/nsai/ocr_quality.py,readonly',
        '--mount',f'type=bind,source={args.output.resolve()},target=/results','--entrypoint','python',IMAGE,'/calibrate.py','--inside','--output','/results']
    if args.blank_only:command.append('--blank-only')
    if args.replay_inputs_only:command.append('--replay-inputs-only')
    raise SystemExit(subprocess.run(command,check=False).returncode)

if __name__=='__main__':main()
