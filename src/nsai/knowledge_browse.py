"""Bounded, freshly authorized navigation of immutable candidate source graphs."""
from collections import Counter
import re
from . import research_store,workflow_store
from .citation_anchors import citation_from_hit

KINDS=frozenset({'all','document','passage','source_span','observation','concept_mention','formula'})


def _load(document_id):
    if not isinstance(document_id,str) or not re.fullmatch('[a-f0-9]{32}',document_id):
        raise ValueError('Invalid source identity')
    artifact=research_store.get(document_id)
    graph=artifact['knowledge']
    if not isinstance(graph.get('nodes'),list) or len(graph['nodes'])>10000 or not isinstance(graph.get('edges'),list) or len(graph['edges'])>40000:
        raise ValueError('Knowledge navigation budget exceeded')
    source=dict(document_id=document_id,revision=artifact['revision'],source_sha256=artifact['source_sha256'],
                artifact_sha256=artifact['artifact_sha256'],graph_sha256=graph['graph_sha256'])
    return artifact,graph,source


def _bounds(offset,limit):
    if type(offset) is not int or not 0<=offset<=40000 or type(limit) is not int or not 1<=limit<=50:
        raise ValueError('Invalid knowledge navigation bounds')


def _item(node):
    text=node['text'];excerpt=text[:1000]
    return dict(id=node['id'],kind=node['kind'],locator=node['locator'],page=node.get('page'),
                excerpt=excerpt,omitted_characters=len(text)-len(excerpt),state='candidate',authority_granted=False)


def page(document_id,*,kind='all',query='',offset=0,limit=25):
    _bounds(offset,limit)
    if kind not in KINDS or not isinstance(query,str) or len(query)>200:raise ValueError('Invalid knowledge filter')
    artifact,graph,source=_load(document_id)
    query=query.strip().casefold()
    nodes=[node for node in graph['nodes'] if (kind=='all' or node['kind']==kind)
           and (not query or query in node['text'].casefold() or query in node['locator'].casefold())]
    degrees=Counter()
    for edge in graph['edges']:
        degrees.update({edge['source_id'],edge['target_id']})
    items=[dict(**_item(node),relationships=degrees[node['id']]) for node in nodes[offset:offset+limit]]
    return dict(source=source,items=items,total=len(nodes),offset=offset,limit=limit,
        next_offset=offset+limit if offset+limit<len(nodes) else None,
        summary=dict(nodes=len(graph['nodes']),relationships=len(graph['edges']),
            node_kinds={kind:sum(node['kind']==kind for node in graph['nodes']) for kind in sorted(KINDS-{'all'})},
            formulas=sum(node['kind']=='formula' for node in graph['nodes']),
            source_processing_complete=graph.get('source_processing_complete') is True,
            extraction_coverage=graph.get('extraction_coverage'),formula_detection_exhaustive=False),
        state='candidate',authority_granted=False,
        limitation='Wording, lexical mentions and quoted formulas do not establish entailment, factual relationships or mathematical correctness.')


def detail(document_id,node_id,*,offset=0,limit=25):
    _bounds(offset,limit)
    if not isinstance(node_id,str) or not re.fullmatch('[a-f0-9]{64}',node_id):raise ValueError('Invalid knowledge node identity')
    artifact,graph,source=_load(document_id)
    nodes={node['id']:node for node in graph['nodes']}
    if node_id not in nodes:raise LookupError('Knowledge node unavailable')
    node=nodes[node_id]
    edges=[edge for edge in graph['edges'] if node_id in {edge['source_id'],edge['target_id']}]
    related=[]
    for edge in edges[offset:offset+limit]:
        other=edge['target_id'] if edge['source_id']==node_id else edge['source_id']
        related.append(dict(id=edge['id'],kind=edge['kind'],direction='outgoing' if edge['source_id']==node_id else 'incoming',
            other=_item(nodes[other]),interpretation_verified=False,authority_granted=False))
    document=workflow_store.source(document_id)
    metadata=document.get('manifest',{}).get('documents',[{}])[0].get('metadata',{})
    hit=dict(id=node['id'],document_id=document_id,title=document['title'],revision=document['revision'],
        original_sha256=document['original_sha256'],media_type=document['media_type'],locator=node['locator'],
        text=node['text'],source_segments=node.get('source_segments',[]),page_coverage=metadata.get('pages'),
        extraction_complete=metadata.get('complete',False) if document['media_type']=='application/pdf' else True)
    return dict(source=source,node=node,citation=citation_from_hit(hit),relationships=related,
        total_relationships=len(edges),offset=offset,limit=limit,next_offset=offset+limit if offset+limit<len(edges) else None,
        state='candidate',authority_granted=False,
        limitation='Quoted source lineage is inspectable. No interpretation, equation evaluation or execution is approved.')
