"""Source-bound candidate knowledge. Heuristics and vectors never confer truth."""
import hashlib
import json
import math
import re

def _id(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode()).hexdigest()

def _source(document_id,revision,source_sha256):
    if not isinstance(document_id,str) or not re.fullmatch('[a-f0-9]{32}',document_id):raise ValueError('Invalid document identity')
    if not isinstance(revision,str) or not 1<=len(revision)<=200:raise ValueError('Invalid source revision')
    if not isinstance(source_sha256,str) or not re.fullmatch('[a-f0-9]{64}',source_sha256):raise ValueError('Invalid source digest')
    return dict(document_id=document_id,revision=revision,source_sha256=source_sha256)

def assemble_knowledge(document_id,revision,source_sha256,spans,*,formula_nodes=None,embeddings=None,max_nodes=10000,max_edges=40000):
    source=_source(document_id,revision,source_sha256)
    if type(max_nodes) is not int or not 1<=max_nodes<=10000 or type(max_edges) is not int or not 1<=max_edges<=40000:raise ValueError('Invalid graph budget')
    if not isinstance(spans,list) or len(spans)>10000:raise ValueError('Invalid span inventory')
    nodes=[];edges=[];seen=set();edge_ids=set();omitted=0;processed_bytes=0
    def node(kind,text,locator,**fields):
        nonlocal omitted
        identity=_id(dict(source=source,kind=kind,text=text,locator=locator,fields=fields))
        if identity in seen:return identity
        if len(nodes)>=max_nodes:omitted+=1;return None
        seen.add(identity)
        match=re.search(r'(?:page[: -]?|p:)(\d+)',locator,re.IGNORECASE)
        nodes.append(dict(id=identity,kind=kind,text=text,locator=locator,source=source,document_id=document_id,source_sha256=source_sha256,
                          page=int(match.group(1)) if match else None,
                          state='candidate',authority_granted=False,**fields))
        return identity
    def edge(left,right,kind,**fields):
        nonlocal omitted
        if left is None or right is None:return
        value=dict(source_id=left,target_id=right,kind=kind,provenance=source,state='candidate',authority_granted=False,**fields)
        value['id']=_id(value)
        if len(edges)>=max_edges:omitted+=1;return
        if value['id'] not in edge_ids:edges.append(value);edge_ids.add(value['id'])
    document=node('document','Source document','document')
    concepts={};span_nodes={};passage_nodes=[]
    passages=[];segments=[];parts=[];size=0;current_page=None
    def flush():
        nonlocal segments,parts,size
        if parts:
            passages.append(('\n'.join(parts),segments))
        segments=[];parts=[];size=0
    for span in spans:
        if not isinstance(span,dict) or not isinstance(span.get('text'),str) or not isinstance(span.get('locator'),str):raise ValueError('Invalid source span')
        match=re.search(r'(?:page[: -]?|p:)(\d+)',span['locator'],re.IGNORECASE)
        page=int(match.group(1)) if match else None
        if parts and page!=current_page:flush()
        current_page=page
        for start in range(0,len(span['text']),599):
            text=span['text'][start:start+599]
            if size+len(text)+(1 if parts else 0)>600:flush()
            segments.append(dict(locator=span['locator'],char_start=start,char_end=start+len(text),text=text))
            parts.append(text);size+=len(text)+(1 if len(parts)>1 else 0)
    flush()
    for text,source_segments in passages:
        passage=node('passage',text,source_segments[0]['locator'],source_segments=source_segments)
        passage_nodes.append((passage,source_segments))
        edge(document,passage,'contains_passage')
    for span in spans:
        if not isinstance(span,dict) or not isinstance(span.get('text'),str) or not isinstance(span.get('locator'),str) or not 1<=len(span['locator'])<=200:raise ValueError('Invalid source span')
        text=span['text'];locator=span['locator']
        processed_bytes+=len(text.encode())
        if processed_bytes>4*1024*1024:raise ValueError('Knowledge source exceeds byte budget')
        if len(text)>32768:raise ValueError('Knowledge span exceeds character budget')
        paragraph=node('source_span',text,locator,extraction='persisted-source-text')
        span_nodes[locator]=paragraph
        edge(document,paragraph,'contains')
        sentences=re.split(r'(?<=[.!?])\s+|\n+',text)
        cursor=0
        for sentence in sentences:
            sentence=sentence.strip()
            if not sentence:continue
            start=text.find(sentence,cursor)
            if start<0:raise ValueError('Observation source offset mismatch')
            end=start+len(sentence);cursor=end
            lower=sentence.lower()
            role=('limitation' if re.search(r'\b(?:limitation|limitations|does not|cannot|fails? to|not supported)\b',lower)
                  else 'definition' if re.search(r'\b(?:defined as|we define|is defined|refers to)\b',lower)
                  else 'method' if re.search(r'\b(?:we propose|we introduce|our method|our approach|we use)\b',lower)
                  else 'result' if re.search(r'\b(?:we show|we find|we demonstrate|results show|results indicate)\b',lower)
                  else 'background')
            # Flags describe wording only, never a claim of semantic understanding.
            observation=node('observation',sentence,locator,char_start=start,char_end=end,source_role=role,role_detection='heuristic',
                negation_cues=re.findall(r'\b(?:no|not|never|without|cannot|neither)\b',lower),
                condition_cues=re.findall(r'\b(?:if|unless|when|provided|assuming|subject to)\b',lower),epistemic_status='unverified_source_observation')
            edge(paragraph,observation,'derived_from_text',entailment_verified=False)
            terms=list(dict.fromkeys(re.findall(r'\b[A-Z][A-Za-z0-9_-]{3,39}\b',sentence)))[:4]
            for term in terms:
                if term in {'this','that','with','from','have','were','been','their','which','there','would','could','should','then','than','into','only','will'}:continue
                key=term
                concept=concepts.get(key)
                if concept is None:
                    concept=node('concept_mention',term,locator,interpretation='lexical-token-only')
                    concepts[key]=concept
                edge(observation,concept,'mentions',relation_verified=False,locator=locator)
    for passage,source_segments in passage_nodes:
        for segment in source_segments:
            edge(passage,span_nodes.get(segment['locator']),'derived_from_span',locator=segment['locator'],char_start=segment['char_start'],char_end=segment['char_end'])
    for formula in formula_nodes or []:
        if not isinstance(formula,dict) or formula.get('source_sha256')!=source_sha256:raise ValueError('Formula source binding mismatch')
        quoted=formula.get('source',{})
        locator=formula.get('locator',quoted.get('locator'))
        if not isinstance(locator,str) or not 1<=len(locator)<=200:raise ValueError('Formula locator required')
        if formula.get('document_id',document_id)!=document_id or formula.get('revision',revision)!=revision:raise ValueError('Formula document identity mismatch')
        expression=formula.get('expression') or formula.get('latex') or quoted.get('text','')
        if not isinstance(expression,str) or len(expression)>8192:raise ValueError('Invalid formula expression')
        item=node('formula',expression,locator,formula_data=formula,epistemic_status='unverified_formula_proposal')
        edge(document,item,'contains_formula',interpretation_verified=False)
        edge(item,span_nodes.get(locator),'derived_from_span',locator=locator,interpretation_verified=False)
    result=dict(schema_version='nsai.knowledge/1',source=source,nodes=nodes,edges=edges,state='candidate',authority_granted=False,
                omissions=omitted,source_processing_complete=omitted==0,semantic_index_status='not_attached',formula_status='attached_unverified' if formula_nodes else 'not_extracted',
                limitations=['Lexical mentions and wording cues do not establish entailment or factual relations.','Automatic evidence projection is separate from independently reviewed canon.'])
    if embeddings is not None:raise ValueError('Use attach_embeddings with explicit model identity and token coverage')
    result['graph_sha256']=_id(result)
    if len(json.dumps(result,ensure_ascii=False,allow_nan=False).encode())>16*1024*1024:raise ValueError('Knowledge JSON exceeds 16MiB budget')
    return result

def _vector(values,dimension=None):
    if not isinstance(values,list) or not 1<=len(values)<=4096 or (dimension is not None and len(values)!=dimension):raise ValueError('Invalid embedding dimensions')
    if any(type(v) not in (int,float) or not math.isfinite(v) for v in values):raise ValueError('Embedding must be finite numeric values')
    norm=math.sqrt(sum(float(v)*float(v) for v in values))
    if not math.isfinite(norm) or norm==0:raise ValueError('Invalid embedding norm')
    # JSONB does not preserve the sign of zero. Keep artifact hashes stable
    # across persistence while storing the same normalized mathematical vector.
    return [float(v)/norm if v else 0.0 for v in values]

def attach_embeddings(graph,vectors,model_identity,coverage):
    if (not isinstance(model_identity,dict) or not isinstance(model_identity.get('name'),str) or not re.fullmatch('[a-f0-9]{64}',model_identity.get('sha256',''))
        or not re.fullmatch('[a-f0-9]{40}',model_identity.get('revision','')) or model_identity.get('dimension')!=384
        or model_identity.get('pooling')!='token-mean-overlap-compensated-special-mean'):raise ValueError('Pinned model identity required')
    if not isinstance(vectors,dict) or not vectors or len(vectors)>10000 or not isinstance(coverage,dict):raise ValueError('Invalid embedding inventory')
    identities={node['id'] for node in graph['nodes'] if node['kind']=='passage'};dimension=384;records=[]
    if identities!=set(vectors) or identities!=set(coverage):raise ValueError('Every passage requires exact embedding and coverage inventory')
    for identity,values in vectors.items():
        if identity not in identities:raise ValueError('Embedding references unknown node')
        vector=_vector(values,dimension);dimension=len(vector)
        item=coverage.get(identity,{})
        if (type(item.get('input_tokens')) is not int or item['input_tokens']<1 or type(item.get('covered_tokens')) is not int or
            item['covered_tokens']!=item['input_tokens'] or item.get('complete') is not True or item.get('max_sequence_length')!=256
            or item.get('pooling')!=model_identity['pooling']):raise ValueError('Invalid token coverage')
        records.append(dict(node_id=identity,vector=vector,coverage=item))
    # JSON roundtrip isolates nested caller state and rejects nonfinite metadata.
    result=json.loads(json.dumps(graph,allow_nan=False))
    result['embeddings']=dict(model_identity=model_identity,dimension=dimension,records=records)
    result['semantic_index_status']='attached-candidate'
    result['graph_sha256']=_id({k:v for k,v in result.items() if k!='graph_sha256'})
    if len(json.dumps(result,ensure_ascii=False,allow_nan=False).encode())>16*1024*1024:raise ValueError('Embedded knowledge exceeds 16MiB budget')
    return json.loads(json.dumps(result,allow_nan=False))

def cosine_search(graph,query_vector,*,model_sha256,top_k=10):
    if type(top_k) is not int or not 1<=top_k<=20:raise ValueError('Invalid search bound')
    index=graph.get('embeddings',{})
    if index.get('model_identity',{}).get('sha256')!=model_sha256:raise ValueError('Embedding model mismatch')
    vector=_vector(query_vector,index['dimension']);nodes={n['id']:n for n in graph['nodes']}
    result=[]
    if len(index['records'])>10000:raise ValueError('Index exceeds search budget')
    for record in index['records']:
        stored=_vector(record['vector'],len(vector));node=nodes[record['node_id']]
        score=max(-1.,min(1.,sum(a*b for a,b in zip(vector,stored))))
        result.append(dict(id=node['id'],node_id=node['id'],text=node['text'],locator=node['locator'],source=node['source'],document_id=node['document_id'],source_sha256=node['source_sha256'],page=node.get('page'),score=score,coverage=record['coverage'],relation='heuristic_semantic_similarity',authority_granted=False))
    return sorted(result,key=lambda r:(-r['score'],r['node_id']))[:top_k]

def memory_projection(graph,*,max_bytes=12000,max_items=12):
    if type(max_bytes) is not int or not 1024<=max_bytes<=16384 or type(max_items) is not int or not 1<=max_items<=32:raise ValueError('Invalid memory budget')
    result=dict(schema_version='nsai.evidence-memory/1',source=graph['source'],evidence=[],canon=[],state='candidate',authority_granted=False,omitted=0)
    for node in graph['nodes']:
        if node['kind'] not in {'observation','formula'}:continue
        result['evidence'].append(node)
        if len(result['evidence'])>max_items or len(json.dumps(result,ensure_ascii=False,allow_nan=False).encode())>max_bytes-128:
            result['evidence'].pop();result['omitted']+=1
    result['serialized_bytes']=0
    for _ in range(8):
        size=len(json.dumps(result,ensure_ascii=False,allow_nan=False).encode())
        if result['serialized_bytes']==size:break
        result['serialized_bytes']=size
    if size>max_bytes:raise ValueError('Memory metadata exceeds byte budget')
    return result
