import React,{useEffect,useState} from 'react';
import {apiRequest} from '../services/api';
import {librarySearchResult} from '../services/libraryContracts';
import {useAuth} from '../state/AuthContext';

const collections=[['Maintenance and procedures','maintenance repair replacement procedure operating instructions'],['Specifications and limits','technical specification operating temperature pressure maximum limit'],['Measurements and data','measurements experimental results dataset observations'],['Research and explanations','research findings methods explanation study']];
export default function LibraryKnowledgeSearch({onSelect}){
 const auth=useAuth();const [draft,setDraft]=useState(''),[query,setQuery]=useState(null),[reload,setReload]=useState(0),[state,setState]=useState(null);
 const key=JSON.stringify([auth.identity.actor,query,reload]);
 useEffect(()=>{
  setState(null);if(!query)return;
  const controller=new AbortController();let alive=true;
  apiRequest('/v1/search?'+new URLSearchParams({q:query}),{signal:controller.signal}).then(librarySearchResult).then(data=>{if(alive)setState({key,data});}).catch(error=>{if(alive&&error.name!=='AbortError')setState({key,error:error.message});});
  return()=>{alive=false;controller.abort();};
 },[key,query]);
 const visible=state?.key===key?state:null;
 const search=value=>{const text=value.trim();if(text){setDraft(text);setQuery(text);setReload(n=>n+1);}};
 return <section className="n-glass rounded-xl p-4 space-y-3" data-testid="library-knowledge-search"><h2 className="font-display text-xl">Find knowledge in uploaded documents</h2><p>Search the content of authorized, indexed sources. Topic collections are live relevance queries, not permanent classifications or factual approval.</p>
  <form className="flex flex-wrap gap-3" onSubmit={event=>{event.preventDefault();search(draft);}}><label className="grow">Question or topic<input aria-label="Library knowledge question" className="n-panel rounded p-2 block w-full" maxLength={1000} value={draft} onChange={event=>setDraft(event.target.value)}/></label><button className="n-cta rounded p-2" type="submit" disabled={!draft.trim()}>Search document knowledge</button></form>
  <div className="flex flex-wrap gap-2" aria-label="Live topic collections">{collections.map(([label,text])=><button className="n-btn-ghost p-2" key={label} onClick={()=>search(text)}>{label}</button>)}</div>
  {query&&!visible&&<p role="status">Searching currently authorized indexed content...</p>}{visible?.error&&<p role="alert">{visible.error}</p>}
  {visible?.data&&<><p data-testid="library-search-method">{visible.data.semantic_state==='ready'?'Lexical + MiniLM semantic retrieval':visible.data.semantic_state==='unavailable'?'Semantic retrieval unavailable; lexical results only':'Lexical retrieval; semantic encoder not configured'}. Up to 12 excerpts; results are not exhaustive.</p>
   {!visible.data.items.length&&<p>No currently indexed, authorized excerpts match. Check source processing readiness or try another question.</p>}
   <ul className="space-y-2" data-testid="library-knowledge-results">{visible.data.items.map(item=><li className="n-panel p-3 rounded space-y-2" key={item.id}><button className="n-btn-ghost text-left p-2 break-all" data-search-source={item.document_id} onClick={()=>onSelect(item.document_id)}>{item.title} - revision {item.revision} - {item.locator}</button><p className="whitespace-pre-wrap break-words">{item.text.slice(0,1200)}{item.text.length>1200?' (excerpt preview; original retained)':''}</p></li>)}</ul>
  </>}
 </section>;
}
