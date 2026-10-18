import React,{useEffect,useState} from 'react';
import { Link,useParams,useNavigate } from 'react-router-dom';
import { useLiveChat } from '../../state/LiveChatContext';
import { useAuth } from '../../state/AuthContext';
import { apiRequest } from '../../services/api';
import { sourceId } from '../../services/libraryContracts';

function Answer({record,loadFull}){
  const [expanded,setExpanded]=useState(false);
  useEffect(()=>setExpanded(false),[record]);
  const answer=record.fullText;
  const receipt=record.receipt;
  const citations=Array.isArray(receipt?.citations)?receipt.citations:[];
  return <article className="n-glass p-4 rounded-xl space-y-3 min-w-0" data-testid="live-chat-answer" data-ai-generated={receipt?.mode==='model_unverified'?'true':'false'}>
    <p>{record.role==='user'?'Retained user question':receipt?.mode==='model_unverified'?'Generated explanation — unverified':'Retained source response — not factual approval'}</p>
    <pre className="whitespace-pre-wrap break-words" data-testid="live-chat-answer-text">{expanded?answer:answer.slice(0,12000)}</pre>
    {receipt?.retrieval_coverage&&<p data-testid="chat-retrieval-method">{receipt.retrieval_coverage.semantic_state==='ready'?'Search used lexical and MiniLM semantic retrieval.':receipt.retrieval_coverage.semantic_state==='unavailable'?'Semantic retrieval was unavailable; search used lexical matches.':'Search method is recorded in the response receipt.'} Retrieved excerpts do not establish exhaustive coverage or factual approval.</p>}
    {record.previewOnly&&<><p>Showing the first {answer.length} of {record.originalLength} retained characters.</p><button className="n-btn-ghost p-2" onClick={()=>loadFull(record.id)}>Load complete retained record</button></>}
    {!record.previewOnly&&answer.length>12000&&<><p>Showing the first 12,000 of {answer.length} characters. The complete response is retained.</p><button className="n-btn-ghost p-2" onClick={()=>setExpanded(value=>!value)}>{expanded?'Show bounded preview':'Show complete retained text'}</button></>}
    {citations.length>0&&<ul className="space-y-2" data-testid="live-chat-citations">{citations.map((citation,index)=><li key={index} className="break-all">
      {sourceId(citation.document_id)?<Link className="underline" to={citation.anchor?.page?`/app/documents/${citation.document_id}`:'/app/library'}
        state={citation.anchor?.page?{anchor:citation.anchor}:{documentId:citation.document_id}}>{citation.title||citation.document_id} · revision {citation.revision} · {citation.locator}</Link>:<span>Unsupported legacy source identifier; inspect the retained receipt.</span>}
    </li>)}</ul>}
    {receipt&&<details><summary>Scope, support and provenance receipt</summary><pre className="whitespace-pre-wrap break-all">{JSON.stringify({mode:receipt.mode,session_id:receipt.session_id,answer_verified:receipt.answer_verified,question_scope:receipt.memory?.source_scope||'unavailable in retained receipt',source_dependencies:receipt.source_dependencies,citation_validation:receipt.citation_validation,support_validation:receipt.support_validation,support_policy_version:receipt.support_policy_version,run_id:receipt.run_id,audit_receipt:receipt.audit_receipt},null,2)}</pre></details>}
  </article>;
}

export default function LiveChatPage(){
  const chat=useLiveChat();const auth=useAuth();const route=useParams();const navigate=useNavigate();
  const [model,setModel]=useState(null);const [modelError,setModelError]=useState(null);
  const [modelRefresh,setModelRefresh]=useState(0);
  const canChat=auth.identity.permissions?.includes('chat');
  useEffect(()=>{
    let alive=true;const active=chat.store.snapshot().activeId;
    (async()=>{await chat.store.loadSessions(null);const current=chat.store.snapshot();if(alive&&!current.pending&&!current.loading){if(route.id&&route.id!==current.activeId)await chat.store.select(route.id);else if(active&&current.activeId===active)await chat.store.loadMessages(null);}})();
    return()=>{alive=false;if(chat.store.snapshot().pending||chat.store.snapshot().loading)chat.store.cancel();};
  },[chat.store,route.id]);
  useEffect(()=>{if(chat.activeId&&!route.id)navigate('/app/chat/'+chat.activeId,{replace:true});},[chat.activeId,route.id,navigate]);
  useEffect(()=>{
    let alive=true;const controller=new AbortController();setModel(null);setModelError(null);
    apiRequest('/v1/model/status',{signal:controller.signal}).then(value=>{if(alive)setModel(value);}).catch(error=>{if(alive&&error.name!=='AbortError')setModelError(error.message);});
    return()=>{alive=false;controller.abort();};
  },[modelRefresh]);
  const generateReady=!!(model?.configured&&model?.reachable&&model?.model_loaded);
  return <section className="p-4 md:p-8 space-y-5 min-w-0" data-testid="live-chat">
    <h1 className="font-display text-2xl">Source-grounded conversation</h1>
    <p>Retrieve evidence across the authorized indexed library or select exact sources. Viewing a citation does not change question scope.</p>
    <div className="flex flex-wrap gap-3">
      <button className="n-cta p-2 rounded" onClick={()=>{chat.store.select(null);navigate('/app/chat');}} data-testid="new-live-conversation">New conversation</button>
      <button className="n-btn-ghost p-2" onClick={()=>chat.store.loadSessions(null)}>Refresh conversation list</button>
      {chat.activeId&&<button className="n-btn-ghost p-2" disabled={chat.pending} onClick={()=>chat.store.loadMessages(null)}>Load latest retained messages</button>}
    </div>
    <p className="break-all" data-testid="live-chat-session">{chat.activeId?`Canonical conversation: ${chat.activeId}`:'New conversation; server identity is assigned when a response is retained.'}</p>
    {chat.unsentDrafts.length>0&&<details><summary>Unsent drafts retained in this tab</summary><ul>{chat.unsentDrafts.map(item=><li key={item.key}><button className="n-btn-ghost p-2 break-all" onClick={()=>{chat.store.resumeDraft(item.key);navigate('/app/chat');}}>Resume unsent: {item.preview}</button></li>)}</ul></details>}
    {chat.sessions&&<details><summary>Your conversations (this page)</summary><ul>{chat.sessions.items.map(item=><li key={item.id}><button className="n-btn-ghost p-2 break-all" data-session-id={item.id} onClick={()=>{chat.store.select(item.id);navigate('/app/chat/'+item.id);}}>{item.created_at} · {item.id}</button></li>)}</ul>
      <button disabled={!chat.sessionCursor} onClick={()=>chat.store.loadSessions(null)}>First conversation page</button>
      <button disabled={!chat.sessions.has_more} onClick={()=>chat.store.loadSessions(chat.sessions.next_cursor)}>Next conversation page</button>
    </details>}
    {chat.messages&&<section className="n-panel p-4 rounded space-y-2" data-testid="live-chat-history">
      <p>{chat.messages.content_policy}</p><ul>{chat.messages.items.map(item=><li key={item.id}><button className="n-btn-ghost p-2 break-all" onClick={()=>chat.store.loadMessage(item.id)} data-message-id={item.id}>{item.role} · {item.created_at} · {item.id}</button></li>)}</ul>
      {!chat.messages.items.length&&<p>No messages are currently readable on this page. Retained records may be withheld by source permissions or incomplete provenance.</p>}
      <button disabled={!chat.messages.has_more||chat.pending} onClick={()=>chat.store.loadMessages(chat.messages.next_before_id)}>Older retained messages</button>
    </section>}
    {chat.error&&<p role="alert">{chat.error}</p>}{chat.notice&&<p role="status" data-testid="live-chat-notice">{chat.notice}</p>}
    {chat.loading&&<p role="status">Loading currently authorized history…</p>}
    {chat.timeline.length>0&&<section className="space-y-3" data-testid="live-chat-timeline"><p>Up to 20 loaded message previews. Older records remain in server history; each answer keeps its original source receipt.</p>{chat.timeline.map(record=>record.unavailable?<p key={record.id} role="status">Retained message {record.id} is currently unavailable: {record.error}</p>:<Answer key={record.id} record={record} loadFull={chat.store.loadMessage}/>)}</section>}
    {chat.selected&&<section data-testid="selected-chat-record"><h2>Selected full retained record</h2><Answer record={chat.selected} loadFull={chat.store.loadMessage}/></section>}
    <section className="n-panel p-4 rounded-xl space-y-3">
      <h2 className="font-display text-xl">Question scope</h2>
      <select aria-label="Question source scope" className="n-glass p-2 max-w-full min-w-0" value={chat.scope.kind} onChange={event=>chat.store.changeScope({kind:event.target.value})}><option value="library">Entire authorized indexed library</option><option value="sources">Explicit sources / revision / pages</option></select>
      {chat.scope.kind==='sources'&&<div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <label className="sm:col-span-2">Exact source IDs (comma-separated, maximum 20)<input aria-label="Chat source IDs" className="n-glass block w-full p-2" value={chat.scope.ids} onChange={event=>chat.store.changeScope({ids:event.target.value})}/></label>
        <label>Optional exact revision<input aria-label="Chat source revision" className="n-glass block w-full p-2" value={chat.scope.revision} onChange={event=>chat.store.changeScope({revision:event.target.value})}/></label>
        <label>Optional PDF pages (comma-separated)<input aria-label="Chat source pages" className="n-glass block w-full p-2" value={chat.scope.pages} onChange={event=>chat.store.changeScope({pages:event.target.value})}/></label>
      </div>}
      <label className="block">Question<textarea aria-label="Live chat question" data-testid="live-chat-question" rows={5} className="n-glass block w-full p-3" value={chat.draft} onChange={event=>chat.store.setDraft(event.target.value)}/></label>
      <p>{Array.from(chat.draft).length}/1,000 characters. Unsent drafts stay only in this tab; server errors do not silently discard them.</p>
      <div className="flex flex-wrap gap-3">
        <button className="n-cta p-2 rounded" disabled={!canChat||chat.pending} onClick={()=>chat.store.send('retrieve')} data-testid="retrieve-chat-evidence">Retrieve source excerpts</button>
        <button className="n-btn-ghost p-2" disabled={!canChat||chat.pending||!generateReady} onClick={()=>chat.store.send('generate')} data-testid="generate-chat-explanation">Generate grounded explanation</button>
        <button className="n-btn-ghost p-2" disabled={!chat.pending&&!chat.loading} onClick={chat.store.cancel}>Cancel browser request</button>
      </div>
      {!generateReady&&<p data-testid="live-chat-model-unavailable">Approved inference is unavailable. Source retrieval remains separate; no model response is fabricated. {modelError||model?.reason||''}</p>}
      <button type="button" className="n-btn-ghost p-2" onClick={()=>setModelRefresh(value=>value+1)}>Refresh inference availability</button>
      <p>Generated text remains unverified. No external voice service is required; local-first streaming voice qualification is still pending.</p>
    </section>
    {chat.recovery.length>0&&<section className="n-panel p-4 rounded space-y-2"><h2>Unresolved request receipts</h2>{chat.recovery.map(item=><div key={item.id} className="break-all"><span>{item.mode} · {item.id}</span><button className="n-btn-ghost p-2" onClick={()=>chat.store.inspectRequest(item.id)}>Check retained request receipt</button></div>)}</section>}
  </section>;
}
