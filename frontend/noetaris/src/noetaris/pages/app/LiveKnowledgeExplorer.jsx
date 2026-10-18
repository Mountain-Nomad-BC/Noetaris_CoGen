import React,{useEffect,useMemo,useState} from 'react';
import {Link,useSearchParams} from 'react-router-dom';
import {ReactFlow,Background,Controls} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import {apiRequest} from '../../services/api';
import {libraryPage,sourceId} from '../../services/libraryContracts';
import {knowledgePage,knowledgeDetail,knowledgeKinds,nodeId} from '../../services/knowledgeContracts';

// Every observation is keyed to its request. Old data cannot render under new filters.
function useProjection(path,validate,args={},refresh=0){
 const encoded=JSON.stringify(args);const key=JSON.stringify([path,encoded,refresh]);
 const [state,setState]=useState({key:null,data:null,error:null});
 useEffect(()=>{
  const controller=new AbortController();let alive=true;
  setState({key,data:null,error:null});
  if(path)apiRequest(path,{signal:controller.signal}).then(value=>validate(value,JSON.parse(encoded))).then(data=>{if(alive)setState({key,data,error:null});}).catch(error=>{if(alive&&error.name!=='AbortError')setState({key,data:null,error:error.message});});
  return()=>{alive=false;controller.abort();};
 },[path,encoded,refresh,validate]);
 return state.key===key?state:{key,data:null,error:null};
}
function Status({value}){return value.error?<p role="alert">{value.error}</p>:!value.data?<p role="status">Loading currently authorized graph data...</p>:null;}
function SourcePicker({selected,choose}){
 const [query,setQuery]=useState(''),[filter,setFilter]=useState(''),[cursor,setCursor]=useState(null),[refresh,setRefresh]=useState(0);
 const params=new URLSearchParams({limit:'25',...(filter?{q:filter}:{}),...(cursor?{cursor}:{})});
 const result=useProjection('/v1/documents?'+params,libraryPage,{},refresh);
 return <section className="n-panel p-4 rounded-xl space-y-3" data-testid="knowledge-source-picker"><h2 className="font-display text-xl">Authorized source library</h2>
  <form className="flex flex-wrap gap-2" onSubmit={event=>{event.preventDefault();setFilter(query);setCursor(null);}}><label>Source title or text<input aria-label="Knowledge source search" className="n-glass block p-2 max-w-full" value={query} maxLength={200} onChange={event=>setQuery(event.target.value)}/></label><button className="n-btn-ghost p-2">Find sources</button></form>
  <button className="n-btn-ghost p-2" onClick={()=>setRefresh(value=>value+1)}>Refresh source readiness</button><Status value={result}/>
  {result.data&&<><p>{result.data.total} authorized sources match. This page shows {result.data.items.length}; indexing readiness does not grant knowledge authority.</p><ul>{result.data.items.map(row=><li className="py-1" key={row.id}><button data-knowledge-source={row.id} aria-pressed={selected===row.id} className="n-btn-ghost p-2 break-all text-left max-w-full" onClick={()=>choose(row.id)}>{row.title} - revision {row.version} - index {row.indexing.state}</button></li>)}</ul>
   <div className="flex flex-wrap gap-2"><button disabled={!cursor} onClick={()=>setCursor(null)}>First source page</button><button disabled={!result.data.has_more} onClick={()=>setCursor(result.data.next_cursor)}>Next source page</button></div></>}
 </section>;
}
function CandidateGraph({page,detail,select}){
 const nodes=useMemo(()=>{
  const values=new Map(page.items.map(row=>[row.id,{id:row.id,kind:row.kind,excerpt:row.excerpt}]));
  if(detail){values.set(detail.node.id,{id:detail.node.id,kind:detail.node.kind,excerpt:detail.node.text});for(const edge of detail.relationships)values.set(edge.other.id,edge.other);}
  return Array.from(values.values()).map((row,index)=>({id:row.id,position:{x:(index%3)*260,y:Math.floor(index/3)*115},data:{label:`${row.kind}: ${row.excerpt.slice(0,90)}`},selected:detail?.node.id===row.id,style:{width:230,background:'#101d30',color:'#e8eef8',border:'1px solid #2e9bff',fontSize:12}}));
 },[page,detail]);
 const edges=useMemo(()=>detail?detail.relationships.map(edge=>({id:edge.id,source:edge.direction==='outgoing'?detail.node.id:edge.other.id,target:edge.direction==='outgoing'?edge.other.id:detail.node.id,label:edge.kind,style:{stroke:'#6885aa'},labelStyle:{fill:'#9daec1',fontSize:10},labelBgStyle:{fill:'#0a1321'}})):[],[detail]);
 return <section><p>Graph of this node page and the selected relationship page. Links describe extraction lineage or lexical relationships, not verified entailment. Select a node to load its authorized details.</p><div className="h-[480px] w-full min-w-0 rounded-xl border border-slate-700" data-testid="live-knowledge-graph"><ReactFlow nodes={nodes} edges={edges} onNodeClick={(_,node)=>select(node.id)} nodesConnectable={false} nodesDraggable={false} fitView proOptions={{hideAttribution:true}}><Background/><Controls showInteractive={false}/></ReactFlow></div></section>;
}
function NodeInspector({detail,select,offset,setOffset}){
 const [expanded,setExpanded]=useState(false);useEffect(()=>setExpanded(false),[detail.node.id]);
 const node=detail.node,citation=detail.citation;
 return <section className="n-panel p-4 rounded-xl space-y-3 min-w-0" data-testid="live-knowledge-inspector">
  <h2 className="font-display text-xl">Candidate {node.kind}</h2><p className="break-all">Node {node.id} - {node.locator}</p>
  <pre className="whitespace-pre-wrap break-words">{expanded?node.text:node.text.slice(0,12000)}</pre>
  {node.text.length>12000&&<><p>Bounded preview: first 12,000 of {node.text.length} text units; complete retained text remains available.</p><button onClick={()=>setExpanded(value=>!value)}>{expanded?'Show bounded preview':'Show complete node text'}</button></>}
  {node.formula_data&&<details data-testid="knowledge-formula-lineage"><summary>Quoted formula and lineage (not evaluated)</summary><pre className="whitespace-pre-wrap break-all">{JSON.stringify(node.formula_data,null,2)}</pre></details>}
  <details><summary>Complete source node record</summary><pre className="whitespace-pre-wrap break-all">{JSON.stringify(node,null,2)}</pre></details>
  <Link className="n-cta inline-flex p-2 rounded" data-testid="knowledge-open-source" to={citation.anchor?.page?`/app/documents/${citation.document_id}`:'/app/library'} state={citation.anchor?.page?{anchor:citation.anchor}:{documentId:citation.document_id}}>Open source evidence</Link>
  <h3>Relationships: {detail.total_relationships} total; showing {detail.relationships.length} at offset {detail.offset}</h3>
  <ul className="space-y-2" data-testid="knowledge-relationships">{detail.relationships.map(edge=><li key={edge.id} className="break-all"><p>{edge.direction}: {edge.kind}; interpretation unverified</p><button className="n-btn-ghost p-2 text-left max-w-full break-all" data-related-node={edge.other.id} onClick={()=>select(edge.other.id)}>{edge.other.kind}: {edge.other.excerpt}</button>{edge.other.omitted_characters>0&&<p>{edge.other.omitted_characters} additional characters retained; open node for complete text.</p>}</li>)}</ul>
  <div className="flex flex-wrap gap-3"><button disabled={offset===0} onClick={()=>setOffset(Math.max(0,offset-25))}>Previous relationship page</button><button disabled={detail.next_offset===null} onClick={()=>setOffset(detail.next_offset)}>Next relationship page</button></div>
  <p>{detail.limitation}</p>
 </section>;
}
function SourceKnowledge({document,initialNode}){
 const [kind,setKind]=useState('all'),[query,setQuery]=useState(''),[filter,setFilter]=useState(''),[offset,setOffset]=useState(0),[selected,setSelected]=useState(initialNode||null),[relationshipOffset,setRelationshipOffset]=useState(0),[view,setView]=useState('list'),[refresh,setRefresh]=useState(0);
 const params=new URLSearchParams({kind,q:filter,offset:String(offset),limit:'25'});
 const page=useProjection(`/v1/knowledge/${document}/browse?${params}`,knowledgePage,{document,offset,kind},refresh);
 const expectedSource=page.data?.source;
 const relatedParams=new URLSearchParams({offset:String(relationshipOffset),limit:'25'});
 const detail=useProjection(expectedSource&&selected?`/v1/knowledge/${document}/nodes/${selected}?${relatedParams}`:null,knowledgeDetail,{document,id:selected,offset:relationshipOffset,expectedSource},refresh);
 const select=id=>{setSelected(id);setRelationshipOffset(0);};
 const reset=()=>{setSelected(null);setRelationshipOffset(0);};
 return <section className="space-y-4 min-w-0" data-testid="live-knowledge-source"><h2 className="font-display text-xl break-all">Source graph: {document}</h2>
  <form className="flex flex-wrap gap-3" onSubmit={event=>{event.preventDefault();setFilter(query);setOffset(0);reset();}}>
   <label>Node kind<select aria-label="Knowledge node kind" className="n-glass block p-2 max-w-full" value={kind} onChange={event=>{setKind(event.target.value);setOffset(0);reset();}}>{knowledgeKinds.map(value=><option key={value}>{value}</option>)}</select></label>
   <label>Literal text / locator<input aria-label="Knowledge node text filter" className="n-glass block p-2 max-w-full" value={query} maxLength={200} onChange={event=>setQuery(event.target.value)}/></label><button className="n-btn-ghost p-2">Filter nodes</button>
  </form>
  <button className="n-btn-ghost p-2" onClick={()=>{reset();setRefresh(value=>value+1);}}>Refresh authorized graph</button><Status value={page}/>
  {page.data&&<><div className="n-glass p-4 rounded-xl space-y-2" data-testid="knowledge-coverage"><p>{page.data.summary.nodes} extracted nodes; {page.data.summary.relationships} relationships; {page.data.summary.formulas} detected formula quotes.</p><p>Source processing {page.data.summary.source_processing_complete?'complete within declared extraction coverage':'incomplete'}. Formula detection is not exhaustive. All displayed graph records remain candidates.</p><p>{page.data.limitation}</p><details><summary>Source identity and extraction coverage</summary><pre className="whitespace-pre-wrap break-all">{JSON.stringify({source:page.data.source,coverage:page.data.summary.extraction_coverage},null,2)}</pre></details></div>
   {page.data.summary.node_kinds&&<section aria-label="Automatically organized source structure" className="n-panel p-4 rounded-xl space-y-2" data-testid="knowledge-organization"><h3>Automatically organized source structure</h3><p>Source-derived records grouped by type. Select a group to inspect its text and relationships.</p><div className="flex flex-wrap gap-2">{Object.entries(page.data.summary.node_kinds).map(([name,count])=><button key={name} className="n-btn-ghost p-2" onClick={()=>{setKind(name);setOffset(0);reset();}}>{name.replaceAll('_',' ')}: {count}</button>)}</div><p>This groups extracted structure; domain folders and topic classifications are not inferred from these counts.</p></section>}
   <p data-testid="knowledge-page-count">{page.data.total} matching nodes; showing {page.data.items.length} at offset {offset}.</p>
   <div className="flex flex-wrap gap-3"><button aria-pressed={view==='list'} onClick={()=>setView('list')}>Node list</button><button aria-pressed={view==='graph'} onClick={()=>setView('graph')}>Graph view</button></div>
   {view==='graph'?<CandidateGraph page={page.data} detail={detail.data} select={select}/>:<ul className="space-y-2" data-testid="live-knowledge-nodes">{page.data.items.map(node=><li className="n-glass p-3 rounded-xl min-w-0" key={node.id}><button className="text-left w-full break-all" data-knowledge-node={node.id} onClick={()=>select(node.id)}><strong>{node.kind}</strong> - {node.locator} - {node.relationships} relationships<p>{node.excerpt}</p></button>{node.omitted_characters>0&&<p>{node.omitted_characters} additional characters retained; open the full node.</p>}</li>)}</ul>}
   {!page.data.items.length&&<p>No currently readable nodes match this filter.</p>}
   <div className="flex flex-wrap gap-3"><button disabled={offset===0} onClick={()=>{setOffset(Math.max(0,offset-25));reset();}}>Previous node page</button><button disabled={page.data.next_offset===null} onClick={()=>{setOffset(page.data.next_offset);reset();}}>Next node page</button></div>
   {selected&&<><Status value={detail}/>{detail.data&&<NodeInspector detail={detail.data} select={select} offset={relationshipOffset} setOffset={setRelationshipOffset}/>}</>}
  </>}
 </section>;
}
export default function LiveKnowledgeExplorer(){
 const [params,setParams]=useSearchParams();const selected=params.get('source');const node=params.get('node');const valid=(!selected||sourceId(selected))&&(!node||(selected&&nodeId(node)));
 return <main className="p-4 md:p-8 space-y-5 min-w-0" data-testid="live-knowledge"><h1 className="font-display text-2xl">Knowledge Atlas</h1><p>Inspect source-bound candidate nodes, formula quotes and extraction relationships. Similarity and wording do not grant factual authority.</p>
  {!valid?<p role="alert">Invalid source identity.</p>:<><SourcePicker selected={selected} choose={id=>setParams({source:id})}/>{selected?<SourceKnowledge key={selected+":"+(node||"")} document={selected} initialNode={node}/>:<p>Select an authorized indexed source to browse its graph.</p>}</>}
 </main>;
}
