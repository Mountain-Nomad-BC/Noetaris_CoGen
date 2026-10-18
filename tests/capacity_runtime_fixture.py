"""Actual generated PDF uploads, isolated parser and encoder, durable publications.

Verified private route functions are exercised directly: the production private
HTTP gate stays closed. Synthetic capacity measurements do not prove relevance.
"""
import argparse
import asyncio
from io import BytesIO
import json
import math
import hashlib
import os
import time
from pathlib import Path
from fastapi import UploadFile
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject,NameObject,DecodedStreamObject
from nsai import api,store,security,semantic_jobs,workflow_store
from semantic_fixture_helpers import configure_authority

PROFILES={'smoke':(2,3),'P0':(100,50),'P1':(1000,50)}


def source(number,pages):
    writer=PdfWriter()
    font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
    for index in range(pages):
        page=writer.add_blank_page(width=612,height=792)
        page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):writer._add_object(font)})})
        text=(f'Motor-{number:03d} maximum operating temperature is {75+number%15} C.' if index==0 else
              f'Motor-{number:03d} synthetic inspection bulletin page {index+1:03d}: record coating wear and inspect insulation.')
        content=DecodedStreamObject();content.set_data(('BT /F1 12 Tf 60 730 Td ('+text+') Tj ET').encode('ascii'))
        page[NameObject('/Contents')]=writer._add_object(content)
    result=BytesIO();writer.write(result);return result.getvalue()


async def run(profile):
    documents,pages=PROFILES[profile]
    configure_authority();identity=security.resolve_principal('Bearer '+Path('/tmp/fixture-user-alice').read_text())
    os.environ.update(NSAI_INDEX_WORKER_ENABLED='true',NSAI_INDEX_CONCURRENCY='2')
    records=[];started=time.perf_counter();sources=[]
    async with api.application_lifespan(api.app):
        for number in range(documents):
            data=source(number,pages);before=time.perf_counter()
            with store.identity_context(identity):
                result=await api.upload(UploadFile(file=BytesIO(data),filename=f'synthetic-capacity-{number:03d}.pdf'),'capacity-1',identity)
            sources.append(result['document_id'])
            records.append(dict(document_id=result['document_id'],bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),upload_seconds=time.perf_counter()-before))
        ingestion_seconds=time.perf_counter()-started
        print(json.dumps(dict(progress=dict(phase='ingested',documents=documents,seconds=ingestion_seconds))),flush=True)
        deadline=time.monotonic()+(1200 if profile=='P1' else 600)
        while True:
            with store.identity_context(identity):
                states=[await asyncio.to_thread(semantic_jobs.source_status,doc) for doc in sources]
            if all(state['ready'] for state in states):break
            if any(state['state']=='failed' for state in states):raise AssertionError('Capacity source indexing failed')
            if time.monotonic()>deadline:raise TimeoutError('Capacity publication deadline exceeded')
            await asyncio.sleep(1)
        publication_seconds=time.perf_counter()-started
        print(json.dumps(dict(progress=dict(phase='published',documents=documents,pages=documents*pages,seconds=publication_seconds,
            memory_peak_bytes=int(Path('/sys/fs/cgroup/memory.peak').read_text())))),flush=True)
    # Complete visibility, source originals and idempotence use actual adapters.
    with store.identity_context(identity):
        seen=[];cursor=None
        while True:
            current=api.documents(limit=25,cursor=cursor,q=None,identity=identity)
            seen.extend(row['id'] for row in current['items']);cursor=current['next_cursor']
            if not cursor:break
        assert set(seen)==set(sources) and len(seen)==documents
        original=source(0,pages)
        duplicate=await api.upload(UploadFile(file=BytesIO(original),filename='same-original.pdf'),'capacity-1',identity)
        assert duplicate['document_id']==sources[0] and duplicate['created'] is False
    samples=[]
    for number in range(4 if profile=='smoke' else 31):
        with store.identity_context(identity):
            before=time.perf_counter()
            hits=await asyncio.to_thread(api.library_retrieve,'Which documents discuss coating wear and insulation inspection?')
            samples.append(dict(seconds=time.perf_counter()-before,hits=len(hits),semantic_state=hits.coverage['semantic_state']))
            print(json.dumps(dict(progress=dict(phase='retrieval',sample=number,**samples[-1]))),flush=True)
            assert hits.coverage['semantic_state']=='ready' and all(hit['document_id'] in sources for hit in hits)
    with store.identity_context(identity):
        hits=await asyncio.to_thread(api.library_retrieve,f'Motor-{documents-1:03d} maximum operating temperature')
        assert hits and {hit['document_id'] for hit in hits}=={sources[-1]}
        matched=workflow_store.claim_context(hits)
        assert any(claim['value'].replace(' ','')==str(75+(documents-1)%15)+'C' for claim in matched)
    bob=security.resolve_principal('Bearer '+Path('/tmp/fixture-user-bob').read_text())
    with store.identity_context(bob):
        assert api.documents(limit=25,cursor=None,q=None,identity=bob)['total']==0
    warm=sorted(sample['seconds'] for sample in samples[1:])
    return dict(status='PASS_SCOPED',profile=profile,documents=documents,pages=documents*pages,
                generated_sources=records,ingestion_seconds=ingestion_seconds,publication_seconds=publication_seconds,
                retrieval_samples=samples,retrieval_first_after_ingestion_seconds=samples[0]['seconds'],
                retrieval_cache_state='Database and encoder used during ingestion; no cold-cache claim',
                retrieval_warm_p50_seconds=warm[math.ceil(len(warm)*.5)-1],
                retrieval_warm_p95_seconds=warm[math.ceil(len(warm)*.95)-1],
                private_sources_hidden_from_second_identity=True,idempotent_upload=True,
                complete_library_pagination=True,capacity_accepted=False,
                client_resources_before_exit=dict(memory_peak_bytes=int(Path('/sys/fs/cgroup/memory.peak').read_text()),
                    cpu_stat=Path('/sys/fs/cgroup/cpu.stat').read_text()),
                limitations=['synthetic native English PDFs','private route/storage adapters; HTTP gate unchanged',
                             'no browser/OCR/LLM contention or held-out retrieval acceptance','performance contract and independent acceptance unassigned'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--profile',choices=PROFILES,required=True)
    arguments=parser.parse_args();print(json.dumps(dict(result=asyncio.run(run(arguments.profile)))))
