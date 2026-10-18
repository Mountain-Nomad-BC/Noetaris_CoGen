"""Prepare a durable, source-linked research corpus using isolated parsing and local CPU semantics.

Originals and derived artifacts stay private. This does not deploy or access the live database.
"""
from pathlib import Path
import argparse
import base64
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
import shutil
import stat
import subprocess
import sys
import time
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from nsai import research_store
from nsai.ingestion import validate_parsed_source
from nsai.source_admission import admit_source_path,admit_filesystem_source,read_source_bytes
from nsai.assembly import strict_json
from nsai.knowledge import attach_embeddings,cosine_search
from nsai.semantic_encoder import LocalSemanticEncoder

# Frozen exploratory queries; topic retrieval is reported, not a general quality qualification.
TOPIC_QUERIES={
 'ai':'How can a computer learn useful patterns from data and make reliable predictions?',
 'physics':'How do physical or quantum systems evolve and what determines their measured behaviour?',
 'computing_systems':'How are computation, distributed processing, scheduling and system resources managed?',
 'economics_business':'How do firms, markets, incentives, costs and economic decisions affect outcomes?',
 'biology':'How do biological organisms, molecular systems and populations change or interact?',
 'mathematics':'What mathematical structures, theorems, probability models and proofs are investigated?',
 'linguistics':'How is human language represented, processed or understood computationally?'}


def sha(data):return hashlib.sha256(data).hexdigest()


def private_file(base,relative):
    admit_source_path(base)
    admit_source_path(relative)
    admit_filesystem_source(base)
    if not isinstance(relative,str) or '\\' in relative:
        raise ValueError('Invalid corpus relative path')
    path=Path(relative)
    if path.anchor or path.is_absolute() or not path.parts or any(p in {'.','..'} or ':' in p for p in path.parts):
        raise ValueError('Corpus path traversal refused')
    target=base
    for part in path.parts:
        target=target/part;info=target.lstat()
        if target.is_symlink() or getattr(info,'st_file_attributes',0)&getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',1024):
            raise ValueError('Corpus source links refused')
    if not target.is_file():raise ValueError('Corpus source is not a regular file')
    return target


def write(path,value):
    raw=json.dumps(value,ensure_ascii=False,sort_keys=True,allow_nan=False,indent=2).encode()
    if len(raw)>32*1024*1024:raise ValueError('Corpus artifact exceeds envelope')
    with path.open('xb') as out:out.write(raw)
    return dict(path=path.name,sha256=sha(raw),bytes=len(raw))


def parse_isolated(data,filename,image):
    import re
    if not re.fullmatch(r'sha256:[a-f0-9]{64}',image):raise ValueError('An exact local image digest is required')
    name='nsai-arxiv-parse-'+uuid4().hex[:12];owner=uuid4().hex
    command=['docker','run','--name',name,'--label','nsai.owner='+owner,'--network','none','--read-only',
        '--cap-drop','ALL','--security-opt','no-new-privileges:true','--user','10001:10001','--cpus','1','--memory','384m',
        '--pids-limit','32','--tmpfs','/tmp:rw,nosuid,nodev,noexec,size=16m,mode=1777','-i',image,'python','-m','nsai.parser_child']
    try:
        result=subprocess.run(command,input=json.dumps(dict(data=base64.b64encode(data).decode(),filename=filename)).encode(),capture_output=True,timeout=25)
        if result.returncode or len(result.stdout)>16*1024*1024:raise ValueError('Isolated parser refused source')
        parsed=json.loads(result.stdout)
        validate_parsed_source(data,parsed)
        return parsed
    finally:
        inspected=subprocess.run(['docker','inspect',name],capture_output=True,timeout=15)
        if inspected.returncode==0:
            info=json.loads(inspected.stdout)[0]
            if info['Config'].get('Labels',{}).get('nsai.owner')!=owner:raise RuntimeError('Unowned parser cleanup refused')
            subprocess.run(['docker','rm','-f',name],capture_output=True,timeout=20,check=True)


def run(manifest_path,image):
    admit_source_path(manifest_path)
    source_manifest=read_source_bytes(manifest_path,8*1024*1024)
    if len(source_manifest)>8*1024*1024:raise ValueError('Oversized corpus manifest')
    source=strict_json(source_manifest,max_bytes=8*1024*1024,max_depth=32,max_items=100000);papers=source['papers']
    if not 1<=len(papers)<=21:raise ValueError('Corpus size outside bounded batch')
    run_id='ingestion-'+uuid4().hex[:12];out=ROOT/'data/arxiv-corpus'/run_id;out.mkdir(parents=True)
    report=dict(run_id=run_id,status='RUNNING',source_manifest_sha256=sha(source_manifest),source_manifest_path=str(manifest_path.relative_to(ROOT)),
        parser_image=image,private_only=True,live_database_accessed=False,semantic_model=None,papers=[],errors=[],
        limits=dict(parser_pdf_bytes=2097152,pages=100,characters=200000,embedding_threads=2,encoder_batch=8),
        scope='Native processing and source custody; no exhaustive formula recognition, scientific truth or independent review claim')
    started=time.monotonic();encoder=LocalSemanticEncoder(ROOT/'state/models/all-MiniLM-L6-v2');report['semantic_model']=encoder.identity
    queries=encoder.encode(list(TOPIC_QUERIES.values()));query_vectors=dict(zip(TOPIC_QUERIES,queries['vectors']))
    query_hits={key:[] for key in TOPIC_QUERIES};centroids={};concept_sets={};map_nodes=[]
    try:
        for paper in papers:
            identity=paper['id'];version=identity;original=read_source_bytes(private_file(manifest_path.parent,paper['pdf_relative_path']),32*1024*1024)
            if len(original)>2097152 or sha(original)!=paper['pdf_sha256']:raise ValueError('Original paper integrity mismatch')
            document_id=sha((version+':'+sha(original)).encode())[:32];folder=out/document_id;folder.mkdir()
            with (folder/'original.pdf').open('xb') as output:output.write(original)
            parsed=parse_isolated(original,document_id+'.pdf',image)
            artifact=research_store.build(document_id,version,parsed);graph=artifact['knowledge']
            passages=[node for node in graph['nodes'] if node['kind']=='passage']
            encoded=encoder.encode([node['text'] for node in passages])
            vectors={node['id']:vector for node,vector in zip(passages,encoded['vectors'])}
            coverage={node['id']:item for node,item in zip(passages,encoded['coverage'])}
            embeddings=dict(vectors=vectors,coverage=coverage,model_identity=encoder.identity)
            embedded=attach_embeddings(graph,**embeddings)
            files={name:write(folder/(name+'.json'),value) for name,value in dict(parsed=parsed,knowledge=graph,
                formulas=artifact['formulas'],memory=graph['memory_projection'],embeddings=embeddings).items()}
            files['original']=dict(path='original.pdf',sha256=sha(original),bytes=len(original))
            weights=[item['input_tokens'] for item in encoded['coverage']];total=sum(weights)
            centroid=[sum(vector[d]*weight for vector,weight in zip(encoded['vectors'],weights))/total for d in range(384)]
            norm=math.sqrt(sum(x*x for x in centroid));centroids[document_id]=[x/norm for x in centroid]
            concept_sets[document_id]={node['text'].casefold() for node in graph['nodes'] if node['kind']=='concept_mention'}
            for topic,vector in query_vectors.items():
                query_hits[topic].extend(cosine_search(embedded,vector,model_sha256=encoder.identity['sha256'],top_k=5))
                query_hits[topic]=sorted(query_hits[topic],key=lambda hit:(-hit['score'],hit['id']))[:5]
            node_counts=dict(Counter(node['kind'] for node in graph['nodes']))
            row=dict(document_id=document_id,arxiv=paper,title=paper['title'],topic=paper['topic'],revision=version,source_sha256=sha(original),
                artifact_sha256=research_store.artifact_hash(artifact),files=files,pages=parsed['page_count'],source_spans=len(parsed['spans']),
                chunks=len(parsed['chunks']),node_counts=node_counts,edges=len(graph['edges']),formula_candidates=len(artifact['formulas']['records']),
                semantic_passages=len(passages),semantic_tokens=sum(weights),all_tokens_covered=all(c['complete'] for c in coverage.values()),
                native_visual_coverage_complete=parsed['complete'],pages_requiring_ocr=[p['page'] for p in parsed['pages'] if not p['complete']],
                independent_review=False,canon_promoted=False)
            report['papers'].append(row);map_nodes.append(dict(id=document_id,title=paper['title'],topic=paper['topic'],source_sha256=sha(original)))
            print(json.dumps(dict(document_id=document_id,topic=paper['topic'],pages=parsed['page_count'],passages=len(passages),formulas=row['formula_candidates'])),flush=True)
        edges=[]
        for left,vector in centroids.items():
            nearby=sorted([(sum(a*b for a,b in zip(vector,other)),right) for right,other in centroids.items() if right!=left],reverse=True)[:3]
            for score,right in nearby:
                shared=sorted(concept_sets[left]&concept_sets[right])
                edges.append(dict(source_id=left,target_id=right,kind='semantic_neighbour_candidate',cosine=score,shared_lexical_mentions=shared[:20],
                    shared_mentions_omitted=max(0,len(shared)-20),model_sha256=encoder.identity['sha256'],entailment_verified=False,authority_granted=False))
        mapping=dict(schema_version='nsai.corpus-map/1',nodes=map_nodes,edges=edges,model_identity=encoder.identity,
            algorithm='Token-count-weighted passage centroid; normalized cosine top3 per document; candidate similarity only',authority_granted=False)
        report['corpus_map']=write(out/'corpus-map.json',mapping)
        report['document_semantics']=write(out/'document-semantics.json',dict(vectors=centroids,model_identity=encoder.identity))
        topics={row['document_id']:row['topic'] for row in report['papers']}
        evaluation={topic:dict(question=TOPIC_QUERIES[topic],hits=hits,expected_topic_in_top5=any(topics[h['document_id']]==topic for h in hits)) for topic,hits in query_hits.items()}
        report['exploratory_semantic_queries']=write(out/'semantic-query-results.json',dict(scope='Frozen broad exploratory queries, not disjoint general-quality acceptance',queries=evaluation))
        counts=dict(Counter(p['topic'] for p in report['papers']));report['topic_counts']=counts
        report['native_visual_coverage_complete']=all(p['native_visual_coverage_complete'] for p in report['papers'])
        report['status']='PREPARED_SCOPED' if len(counts)>=5 and all(2<=count<=3 for count in counts.values()) else 'PARTIAL_CORPUS'
    except Exception as error:
        report['status']='FAIL';report['errors'].append(dict(type=type(error).__name__,message=str(error)[:300]))
        raise
    finally:
        report['elapsed_seconds']=time.monotonic()-started;report['captured_at']=datetime.now(timezone.utc).isoformat()
        write(out/'manifest.json',report)
        evidence=ROOT/'evidence/arxiv-ingestion';evidence.mkdir(parents=True,exist_ok=True)
        write(evidence/(run_id+'.json'),report)
        print(json.dumps(dict(status=report['status'],manifest=str((out/'manifest.json').relative_to(ROOT)),papers=len(report['papers']))),flush=True)
    return 0 if report['status']=='PREPARED_SCOPED' else 1


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--manifest',type=Path,required=True);cli.add_argument('--parser-image',required=True)
    options=cli.parse_args();raise SystemExit(run(options.manifest.resolve(),options.parser_image))
