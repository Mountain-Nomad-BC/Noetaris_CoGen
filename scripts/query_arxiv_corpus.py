"""Ask a prepared private research corpus using its pinned CPU encoder and provenance graph."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from ingest_arxiv_corpus import private_file,sha
from nsai.knowledge import attach_embeddings,cosine_search
from nsai.semantic_encoder import LocalSemanticEncoder
from nsai.source_admission import admit_source_path,read_source_bytes
from nsai.assembly import strict_json


def load_artifact(folder,row,key):
    entry=row['files'][key];raw=read_source_bytes(private_file(folder,entry['path']),32*1024*1024)
    if len(raw)>32*1024*1024 or sha(raw)!=entry['sha256']:raise ValueError('Corpus artifact byte identity mismatch')
    return strict_json(raw,max_bytes=32*1024*1024,max_depth=32,max_items=1000000)


def query(manifest,question,*,topic=None,limit=6,enrichment_manifest=None):
    admit_source_path(manifest)
    if enrichment_manifest is not None:admit_source_path(enrichment_manifest)
    if not isinstance(question,str) or not 1<=len(question)<=1000 or not 1<=limit<=20:raise ValueError('Invalid bounded question')
    raw=read_source_bytes(manifest,8*1024*1024)
    if len(raw)>8*1024*1024:raise ValueError('Corpus manifest exceeds limit')
    corpus=strict_json(raw,max_bytes=8*1024*1024,max_depth=32,max_items=100000);encoder=LocalSemanticEncoder(ROOT/'state/models/all-MiniLM-L6-v2')
    if encoder.identity!=corpus['semantic_model']:raise ValueError('Corpus/query encoder identity differs')
    vector=encoder.encode([question])['vectors'][0];hits=[];details={}
    supplemental={}
    if enrichment_manifest:
        enrichment=strict_json(read_source_bytes(enrichment_manifest,8*1024*1024),max_bytes=8*1024*1024,max_depth=32,max_items=100000)
        if enrichment['prepared_manifest_sha256']!=sha(raw):raise ValueError('Supplement/corpus generation mismatch')
        supplemental={row['document_id']:row for row in enrichment['papers']}
    for row in corpus['papers']:
        if topic and row['topic']!=topic:continue
        folder=manifest.parent/row['document_id']
        graph=load_artifact(folder,row,'knowledge');embeddings=load_artifact(folder,row,'embeddings')
        graph=attach_embeddings(graph,**embeddings)
        found=cosine_search(graph,vector,model_sha256=encoder.identity['sha256'],top_k=min(limit,20))
        nodes={n['id']:n for n in graph['nodes']}
        formulas=load_artifact(folder,row,'formulas')['records']
        for hit in found:
            passage=nodes[hit['id']];locators={s['locator'] for s in passage['source_segments']}
            hit.update(title=row['title'],topic=row['topic'],arxiv_url=row['arxiv']['abstract_url'],
                source_segments=passage['source_segments'],extraction_coverage=graph['extraction_coverage'],
                formula_candidates=[f for f in formulas if f['source']['locator'] in locators],
                graph_links=[e for e in graph['edges'] if e['source_id']==hit['id'] or e['target_id']==hit['id']])
            details[hit['id']]=hit
        hits.extend(found)
        for supplement in supplemental.get(row['document_id'],{}).get('supplements',[]):
            if not supplement.get('files'):continue
            location=enrichment_manifest.parent/row['document_id']/supplement['folder']
            supplemental_graph=load_artifact(location,supplement,'knowledge')
            supplemental_embeddings=load_artifact(location,supplement,'embeddings')
            supplemental_graph=attach_embeddings(supplemental_graph,**supplemental_embeddings)
            nodes={n['id']:n for n in supplemental_graph['nodes']}
            for hit in cosine_search(supplemental_graph,vector,model_sha256=encoder.identity['sha256'],top_k=limit):
                hit.update(title=row['title'],topic=row['topic'],arxiv_url=row['arxiv']['abstract_url'],
                    extraction_kind=supplement['kind'],quality_verified=False,source_segments=nodes[hit['id']]['source_segments'],
                    extraction_artifact_sha256=supplement['extraction']['sha256'],
                    graph_links=[e for e in supplemental_graph['edges'] if e['source_id']==hit['id'] or e['target_id']==hit['id']])
                hits.append(hit)
    hits=sorted(hits,key=lambda hit:(-hit['score'],hit['id']))[:limit]
    return dict(question=question,method='pinned-pretrained-semantic-cosine-with-source-graph',model_identity=encoder.identity,
        hits=hits,answer_verified=False,authority_granted=False,
        memory=dict(state='query-evidence-candidates',canon=[],evidence_ids=[h['id'] for h in hits]),
        limitations=['Similarity is not entailment or mathematical verification.','Native visual/OCR coverage is reported for every hit.','No generated answer or scientific truth certification is implied.'])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);group=p.add_mutually_exclusive_group(required=True);group.add_argument('--manifest',type=Path);group.add_argument('--current',action='store_true');p.add_argument('--question',required=True);p.add_argument('--topic');p.add_argument('--limit',type=int,default=6);p.add_argument('--enrichment-manifest',type=Path)
    a=p.parse_args();enrichment=a.enrichment_manifest
    if a.current:
        catalog=json.loads((ROOT/'data/arxiv-corpus/current.json').read_bytes())
        manifest=private_file(ROOT,catalog['prepared_manifest']['path'])
        if sha(manifest.read_bytes())!=catalog['prepared_manifest']['sha256']:raise ValueError('Current corpus catalog binding mismatch')
        if not enrichment and catalog.get('enrichment_manifest'):
            enrichment=private_file(ROOT,catalog['enrichment_manifest']['path'])
            if sha(enrichment.read_bytes())!=catalog['enrichment_manifest']['sha256']:raise ValueError('Current supplement catalog binding mismatch')
    else:manifest=a.manifest.resolve()
    print(json.dumps(query(manifest,a.question,topic=a.topic,limit=a.limit,enrichment_manifest=enrichment.resolve() if enrichment else None),ensure_ascii=False,indent=2,allow_nan=False))
