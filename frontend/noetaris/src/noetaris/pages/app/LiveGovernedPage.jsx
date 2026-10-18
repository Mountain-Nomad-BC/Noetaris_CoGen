import React,{useEffect,useMemo,useState} from 'react';
import {Link,useSearchParams} from 'react-router-dom';
import {useAuth} from '../../state/AuthContext';
import {useLiveGoverned} from '../../state/LiveGovernedContext';
import {apiRequest} from '../../services/api';
import {governedId,governedPage} from '../../services/governedContracts';
import {sourceId} from '../../services/libraryContracts';
const kinds=['all','assembly','issues','proposal','extraction'],states=['all','candidate','reviewed','rejected'];
function CandidateList({principal,kind,state,choose}){
 const [cursor,setCursor]=useState(null),[result,setResult]=useState({data:null,error:null});
 useEffect(()=>{
  const controller=new AbortController();let alive=true;setResult({data:null,error:null});
  const query=new URLSearchParams({limit:'25',kind,state,...(cursor?{cursor}:{})});
  apiRequest('/v1/governed/records?'+query,{signal:controller.signal}).then(value=>governedPage(value,{...principal,kind,state})).then(data=>{if(alive)setResult({data,error:null});}).catch(error=>{if(alive&&error.name!=='AbortError')setResult({data:null,error:error.message});});
  return()=>{alive=false;controller.abort();};
 },[cursor,principal.actor,principal.reviewer,kind,state]);
 return <section className="n-panel rounded-xl p-4 space-y-3" data-testid="governed-candidate-list">
  <h2 className="font-display text-xl">Retained candidates</h2>
  {result.error?<p role="alert">{result.error}</p>:!result.data?<p role="status">Loading currently authorized candidates...</p>:<>
   <p>{result.data.total} visible records at the latest count; showing {result.data.items.length}. {result.data.limitation} This list is not a fixed snapshot.</p>
   {!result.data.items.length&&<p>No retained candidates in this authorized view.</p>}
   <ul className="space-y-2">{result.data.items.map(row=><li className="n-glass p-3 rounded break-all" key={row.id}><button className="text-left max-w-full" data-governed-record={row.id} onClick={()=>choose(row.id)}>{row.kind} - {row.state}<p>{row.id}</p><p>Author {row.author}; origin {row.document_id}</p></button></li>)}</ul>
   <div className="flex flex-wrap gap-3"><button disabled={!cursor} onClick={()=>setCursor(null)}>First candidate page</button><button disabled={!result.data.has_more} onClick={()=>setCursor(result.data.next_cursor)}>Next candidate page</button></div>
  </>}
 </section>;
}
function Payload({value,store}){
 const raw=useMemo(()=>JSON.stringify(value,null,2),[value]);const [expanded,setExpanded]=useState(false);
 useEffect(()=>{if(raw.length<=12000)store.inspectPayload();},[raw,store]);
 return <section className="n-glass p-3 rounded space-y-2" data-testid="governed-payload">
  <h3 className="font-display text-lg">Immutable candidate payload</h3>
  {raw.length>12000&&!expanded&&<p>A bounded preview is shown. Display the complete retained payload before acknowledging review.</p>}
  <pre className="whitespace-pre-wrap break-all" data-testid="governed-payload-text">{expanded?raw:raw.slice(0,12000)}</pre>
  {raw.length>12000&&<button onClick={()=>{setExpanded(value=>!value);store.inspectPayload();}}>{expanded?'Collapse payload preview':'Display complete retained payload'}</button>}
 </section>;
}
function Outcome({review}){
 const value=review.outcome;if(!value)return null;
 return <section className="n-glass rounded-xl p-4 break-all space-y-2" data-testid="governed-outcome">
  {value.status==='pending'?<p role="status">Independent decision pending for {value.record.id}. The captured request survives ordinary source navigation.</p>:value.status==='confirmed'?<p role="status">Confirmed {value.receipt.record_id}: {value.receipt.state}. Audit receipt {value.receipt.audit_receipt}. No execution or canonical authority was granted.</p>:value.status==='observed'?<p role="status">Fresh server state observed for {value.observed.id}: {value.observed.state}; review ID {value.observed.review_id||'none'}. This does not attribute the original request or supply an audit receipt for it.</p>:<><p role="alert">The decision response for {value.record.id} is unconfirmed. Do not automatically repeat it. Read the retained record to inspect current state.</p><button disabled={review.busy} onClick={review.store.archive}>Retain uncertain snapshot and continue</button></>}
  <details><summary>Captured local request and result</summary><pre className="whitespace-pre-wrap break-all">{JSON.stringify(value,null,2)}</pre></details>
 </section>;
}
function Inspector({review,principal}){
 const value=review.data;
 return <section className="n-panel p-4 rounded-xl space-y-4 min-w-0" data-testid="governed-inspector">
  <h2 className="font-display text-xl">Candidate inspection</h2><p className="break-all">{review.activeId}</p><button disabled={review.loading||review.busy} onClick={()=>review.store.load(review.activeId,principal)}>Read current retained record</button>
  {review.loading?<p role="status">Reading current source-authorized candidate...</p>:value?<>
   <p>{value.kind}; {value.state}; author {value.author}. Independent review records a decision; it does not authorize generated code, provider dispatch, canonical promotion or execution.</p>
   <div className="n-glass p-3 rounded break-all"><h3>Origin and complete retained dependencies</h3><p>{value.source.title}; revision {value.source.revision}; source SHA256 {value.source_sha256}.</p><p>Origin byte binding: {value.source_integrity_matches?'matches retained original':'unavailable or mismatched'}. Provenance: {value.provenance_complete?'recorded complete':'incomplete; review unavailable'}.</p><ul>{value.source_ids.map(id=><li key={id}>{sourceId(id)?<Link className="underline" to="/app/library" state={{documentId:id}}>Inspect original {id}</Link>:<span>{id} - legacy source inspection requires its source API.</span>}</li>)}</ul></div>
   <Payload key={value.id} value={value.payload} store={review.store}/>
   {value.review&&<section className="n-glass p-3 rounded break-all" data-testid="governed-retained-review"><h3>Retained independent review</h3><p>Exact review ID {value.review.id}; {value.review.decision}; reviewer {value.review.actor}; {value.review.created_at}.</p><pre className="whitespace-pre-wrap break-words">{value.review.rationale}</pre></section>}
   <label className="block">Independent review rationale<textarea aria-label="Governed candidate rationale" className="n-glass block w-full p-3" rows={4} value={review.notes[value.id]||''} onChange={event=>review.store.note(value.id,event.target.value)}/></label>
   <p>{Array.from(review.notes[value.id]||'').length}/2,000 characters. Tab drafts survive source navigation and clear on identity change or browser reload. Server review history is retained separately.</p>
   <label className="flex items-start gap-2"><input aria-label="Acknowledge governed candidate inspection" type="checkbox" disabled={!value.can_review||!review.payloadInspected||review.busy} checked={review.acknowledged} onChange={event=>review.store.acknowledge(event.target.checked)}/><span>I inspected the relevant originals and complete retained payload, and understand this grants no execution or canonical authority.</span></label>
   {!value.can_review&&<p>Independent review is unavailable for this identity, self-authored or closed record, or incomplete source binding.</p>}
   <div className="flex flex-wrap gap-3">{[['reviewed','Record independent review'],['rejected','Reject candidate']].map(([decision,label])=><button className="n-btn-ghost p-2" data-governed-decision={decision} key={decision} disabled={!value.can_review||!review.payloadInspected||!review.acknowledged||review.busy||review.outcome?.status==='uncertain'} onClick={()=>review.store.decide(decision,principal)}>{label}</button>)}</div>
  </>:<p>A fresh authorized read is required. Stored candidates, originals and prior reviews are retained.</p>}
 </section>;
}
export default function LiveGovernedPage(){
 const auth=useAuth(),review=useLiveGoverned();const [params,setParams]=useSearchParams(),[refresh,setRefresh]=useState(0);
 const principal={actor:auth.identity.actor,reviewer:['reviewer','admin'].includes(auth.identity.role)&&auth.identity.permissions?.includes('review')===true};
 const requested=params.get('record'),kind=params.get('kind')||'all',state=params.get('state')||'all',valid=(requested===null||governedId(requested))&&kinds.includes(kind)&&states.includes(state);
 useEffect(()=>{review.store.open(valid?(requested||review.store.snapshot().activeId):null,principal);return()=>review.store.leave();},[requested,valid,principal.actor,principal.reviewer,review.store]);
 useEffect(()=>{if(['confirmed','observed'].includes(review.outcome?.status))setRefresh(value=>value+1);},[review.outcome?.status,review.outcome?.receipt?.audit_receipt,review.outcome?.observed?.review_id]);
 const update=(name,value)=>{const next=new URLSearchParams(params);next.set(name,value);setParams(next);};
 return <main className="p-4 md:p-8 space-y-5 min-w-0" data-testid="live-governed-candidates">
  <h1 className="font-display text-2xl">Governed candidate review</h1><p>Inspect retained source-bound candidates and independent review history. Policy changes, execution permissions, promotion and workflow publication are separate controls.</p>
  {!valid?<p role="alert">Invalid candidate identity or navigation filter.</p>:<>
   <div className="flex flex-wrap items-end gap-3"><label>Candidate kind<select aria-label="Governed candidate kind" value={kind} onChange={event=>update('kind',event.target.value)}>{kinds.map(item=><option key={item} value={item}>{item}</option>)}</select></label><label>Review state<select aria-label="Governed candidate state" value={state} onChange={event=>update('state',event.target.value)}>{states.map(item=><option key={item} value={item}>{item}</option>)}</select></label><button onClick={()=>setRefresh(value=>value+1)}>Refresh candidate list from first page</button></div>
   <CandidateList key={`${principal.actor}:${principal.reviewer}:${kind}:${state}:${refresh}`} principal={principal} kind={kind} state={state} choose={id=>update('record',id)}/>
  </>}
  {review.error&&<p role="alert">{review.error}</p>}<Outcome review={review}/>
  {Object.keys(review.notes).length>0&&<details data-testid="governed-rationale-drafts"><summary>Retained rationale drafts ({Object.keys(review.notes).length})</summary><ul>{Object.entries(review.notes).map(([id,text])=><li className="n-glass p-3 break-all" key={id}><p>{id}</p><pre className="whitespace-pre-wrap break-words">{text}</pre><button disabled={review.busy} onClick={()=>review.store.note(id,'')}>Clear this governed rationale explicitly</button></li>)}</ul></details>}
  {review.archives.length>0&&<details data-testid="governed-archived-attempts"><summary>Retained uncertain requests ({review.archives.length})</summary><ul>{review.archives.map((attempt,index)=><li className="n-glass p-3 break-all" key={index}><p>{attempt.record.id}: {attempt.status}; observed state does not attribute the original request.</p><pre className="whitespace-pre-wrap break-all">{JSON.stringify(attempt,null,2)}</pre><button disabled={attempt.status==='uncertain'||review.busy} onClick={()=>review.store.clearArchive(index)}>Clear resolved governed snapshot explicitly</button></li>)}</ul></details>}
  {valid&&review.activeId&&<Inspector review={review} principal={principal}/>}
 </main>;
}
