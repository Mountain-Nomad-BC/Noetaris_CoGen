"""Development measurement over existing private originals, not held-out acceptance."""
import argparse
import asyncio
from io import BytesIO
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import time
import traceback
from fastapi import UploadFile
from nsai import api,store,security,semantic_jobs,workflow_store
from semantic_fixture_helpers import configure_authority

# Previously published exploratory questions; deliberately not called held-out.
QUERIES={
 'ai':'How can a computer learn useful patterns from data and make reliable predictions?',
 'physics':'How do physical or quantum systems evolve and what determines their measured behaviour?',
 'computing_systems':'How are computation, distributed processing, scheduling and system resources managed?',
 'economics_business':'How do firms, markets, incentives, costs and economic decisions affect outcomes?',
 'biology':'How do biological organisms, molecular systems and populations change or interact?',
 'mathematics':'What mathematical structures, theorems, probability models and proofs are investigated?',
 'linguistics':'How is human language represented, processed or understood computationally?'}


def ranking_metrics(ranked,expected,k=5):
    if not expected or not 1<=k<=50:raise ValueError('Nonempty relevance set and bounded rank required')
    documents=list(dict.fromkeys(ranked))
    relevant=set(expected)
    found=len(set(documents[:k])&relevant)
    return dict(recall_at_k=found/len(relevant),precision_at_k=found/k,
                reciprocal_rank=next((1/index for index,item in enumerate(documents,1) if item in relevant),0),
                k=k,rank_unit='unique document; first occurrence retained')


def original(folder,row):
    relative=PurePosixPath(row['pdf_relative_path'])
    if relative.is_absolute() or len(relative.parts)!=1 or '\\' in str(relative):raise ValueError('Unexpected corpus path')
    path=folder/relative.name
    if path.is_symlink() or not path.is_file():raise ValueError('Corpus original unavailable')
    data=path.read_bytes()
    if len(data)!=row['pdf_bytes'] or hashlib.sha256(data).hexdigest()!=row['pdf_sha256']:raise ValueError('Corpus original identity mismatch')
    return data


async def run():
    folder=Path('/corpus');manifest=json.loads((folder/'manifest.json').read_bytes())
    papers=manifest['papers']
    assert len(papers)==14 and {row['topic'] for row in papers}==set(QUERIES)
    configure_authority()
    alice=security.resolve_principal('Bearer '+Path('/tmp/fixture-user-alice').read_text())
    bob=security.resolve_principal('Bearer '+Path('/tmp/fixture-user-bob').read_text())
    os.environ.update(NSAI_INDEX_WORKER_ENABLED='true',NSAI_INDEX_CONCURRENCY='2')
    records=[];started=time.perf_counter()
    async with api.application_lifespan(api.app):
        for row in papers:
            data=original(folder,row)
            print(json.dumps(dict(progress=dict(phase='upload-start',input_sha256=row['pdf_sha256'],
                expected_pages=row['ingestion_preflight']['page_count'],accepted_documents=len(records)))),flush=True)
            with store.identity_context(alice):
                try:
                    result=await api.upload(UploadFile(file=BytesIO(data),filename=row['pdf_relative_path']),'corpus-development-1',alice)
                except Exception as error:
                    # Preserve the internal boundary behind the deliberately
                    # generic public 503 without exposing source text or secrets.
                    cause=error.__context__ or error
                    print(json.dumps(dict(diagnostic=dict(input_sha256=row['pdf_sha256'],
                        error_type=type(cause).__name__,sqlstate=getattr(cause,'sqlstate',None),
                        frames=traceback.format_tb(cause.__traceback__)))),flush=True)
                    raise
                metadata=workflow_store.source(result['document_id'])
                pages=metadata['manifest']['documents'][0]['metadata']['pages']
                assert len(pages)==row['ingestion_preflight']['page_count']
            records.append(dict(document_id=result['document_id'],topic=row['topic'],pages=len(pages),
                original_sha256=row['pdf_sha256'],bytes=len(data),
                incomplete_pages=sum(not page.get('complete',False) for page in pages)))
        ingestion_seconds=time.perf_counter()-started
        print(json.dumps(dict(progress=dict(phase='ingested',documents=len(records),seconds=ingestion_seconds))),flush=True)
        deadline=time.monotonic()+600
        while True:
            with store.identity_context(alice):
                states=[await asyncio.to_thread(semantic_jobs.source_status,row['document_id']) for row in records]
            if all(state['ready'] for state in states):break
            if any(state['state']=='failed' for state in states):raise AssertionError('Research corpus indexing failed')
            if time.monotonic()>deadline:raise TimeoutError('Research corpus publication deadline')
            await asyncio.sleep(.5)
    publication_seconds=time.perf_counter()-started
    sources={row['document_id'] for row in records};comparisons=[]
    with store.identity_context(alice):
        listed=api.documents(limit=25,cursor=None,q=None,identity=alice)
        assert listed['total']==14 and {row['id'] for row in listed['items']}==sources
        for row in records:
            data,media=workflow_store.original_source(row['document_id'])
            assert media=='application/pdf' and hashlib.sha256(data).hexdigest()==row['original_sha256']
        for topic,question in QUERIES.items():
            measurements={}
            for name,retrieve in [('lexical',workflow_store.retrieve),('hybrid',api.library_retrieve)]:
                before=time.perf_counter();hits=await asyncio.to_thread(retrieve,question)
                seconds=time.perf_counter()-before
                assert all(hit['document_id'] in sources for hit in hits)
                if name=='hybrid':assert hits.coverage.get('semantic_state')=='ready'
                expected={row['document_id'] for row in records if row['topic']==topic}
                measurements[name]=dict(seconds=seconds,metrics=ranking_metrics([hit['document_id'] for hit in hits],expected),
                    hits=[dict(chunk_id=hit['id'],document_id=hit['document_id'],locator=hit['locator']) for hit in hits],coverage=hits.coverage)
            response=await asyncio.to_thread(api.chat,api.Question(question=question),alice)
            assert response['answer_verified'] is False and all(item['document_id'] in sources for item in response['citations'])
            comparisons.append(dict(topic=topic,question=question,methods=measurements,
                ordinary_chat=dict(mode=response['mode'],citation_count=len(response['citations']),answer_verified=False)))
            print(json.dumps(dict(progress=dict(phase='paired-retrieval',topic=topic))),flush=True)
    with store.identity_context(bob):
        assert api.documents(limit=25,cursor=None,q=None,identity=bob)['total']==0
        assert not await asyncio.to_thread(api.library_retrieve,QUERIES['ai'])
    return dict(status='PASS_SCOPED',profile='arxiv-development',documents=len(records),pages=sum(row['pages'] for row in records),
        originals=records,ingestion_seconds=ingestion_seconds,publication_seconds=publication_seconds,comparisons=comparisons,
        capacity_accepted=False,retrieval_quality_accepted=False,private_http_admitted=False,
        label_scope='Existing sample topic membership only; overlapping topics and passage relevance were not independently judged. Questions are previously published development inputs.',
        client_resources_before_exit=dict(memory_peak_bytes=int(Path('/sys/fs/cgroup/memory.peak').read_text()),cpu_stat=Path('/sys/fs/cgroup/cpu.stat').read_text()),
        limitations=['Private direct application adapters, not admitted individual-user HTTP',
            'Native extraction only; incomplete visual/OCR pages remain explicit',
            'No generated explanation, scientific/mathematical verification, independent held-out quality or SLO acceptance'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--profile',choices=['arxiv-development'],required=True);parser.parse_args()
    print(json.dumps(dict(result=asyncio.run(run()))))
