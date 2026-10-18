import assert from 'node:assert/strict';
import { test } from 'node:test';
import { questionRequest,chatResult,historyMessage,messageId,libraryScope } from '../src/noetaris/services/chatContracts.js';
import { LiveChatStore } from '../src/noetaris/services/liveChatStore.js';
const sid='a'.repeat(32),source='b'.repeat(32);
const page={items:[],has_more:false,next_cursor:null};
function reply(body){return {session_id:body.session_id||sid,answer:'Real response shape',mode:'evidence-extract',answer_verified:false,provenance_complete:true,citations:[],source_dependencies:body.document_ids,memory:{source_scope:{document_ids:body.document_ids,revision:body.revision,pages:body.pages}}};}
test('question text and explicit source/page choices are preserved without document-count truncation',()=>{
  const body=questionRequest('  exact question\n',{kind:'sources',ids:source+', '+source,revision:' 1',pages:'2,1,2'},null,'c'.repeat(32));
  assert.equal(body.question,'  exact question\n');assert.equal(body.revision,' 1');assert.deepEqual(body.document_ids,[source]);assert.deepEqual(body.pages,[1,2]);
  const many=Array.from({length:21},(_,i)=>i.toString(16).padStart(32,'0')).join(',');
  assert.throws(()=>questionRequest('q',{kind:'sources',ids:many,revision:'',pages:''},null,'c'.repeat(32)),/1–20/);
  assert.throws(()=>questionRequest('q',{kind:'sources',ids:source,revision:'',pages:'1.5'},null,'c'.repeat(32)));
  assert.throws(()=>questionRequest('x'.repeat(1001),libraryScope(),null,'c'.repeat(32)));
});
test('response cannot cross canonical conversation or question source boundaries',()=>{
  const body=questionRequest('q',{kind:'sources',ids:source,revision:'1',pages:'2'},sid,'c'.repeat(32));const valid=reply(body);
  assert.equal(chatResult(valid,body),valid);
  for(const change of [{session_id:'d'.repeat(32)},{source_dependencies:['e'.repeat(32)]},{memory:{source_scope:{...valid.memory.source_scope,pages:[1]}}},{answer_verified:true}])assert.throws(()=>chatResult({...valid,...change},body));
});
test('retained message reads full receipt instead of historical text prefix and keeps IDs exact',()=>{
  const id='9007199254740993';assert.equal(messageId(id),true);assert.equal(messageId(Number(id)),false);
  const record=historyMessage({session_id:sid,id,role:'assistant',provenance_complete:true,text_preview:'prefix',receipt:{answer:'x'.repeat(20000)},full_text_field:'receipt.answer'},sid,id);
  assert.equal(record.fullText.length,20000);
  assert.throws(()=>historyMessage({...record,session_id:'e'.repeat(32)},sid,id));
});
test('first response binds canonical session and next turn reuses it',async()=>{
  const bodies=[];const store=new LiveChatStore(async(path,options)=>{if(path.startsWith('/v1/chat/sessions?'))return page;bodies.push(options.body);return reply(options.body);});
  store.setDraft('first');await store.send('retrieve');store.setDraft('second');await store.send('retrieve');
  assert.equal(bodies[0].session_id,null);assert.equal(bodies[1].session_id,sid);assert.notEqual(bodies[0].request_id,bodies[1].request_id);
  assert.equal(store.snapshot().timeline.length,4);assert.equal(store.snapshot().draft,'');
});
test('scope switch rejects late response even if transport ignores abort; recovery never attaches it to a new conversation',async()=>{
  let complete,body;
  const store=new LiveChatStore(async(path,options)=>{
    if(path.startsWith('/v1/chat/sessions?'))return page;
    if(path.startsWith('/v1/invocations/'))return {state:'completed',response:reply(body)};
    body=options.body;return await new Promise(resolve=>{complete=resolve;});
  });
  store.setDraft('old request');const pending=store.send('retrieve');const request=store.snapshot().recovery[0];
  store.changeScope({kind:'sources',ids:source});await store.select(null);store.setDraft('new unsent question');complete(reply(body));await pending;
  assert.equal(store.snapshot().timeline.length,0);assert.equal(store.snapshot().draft,'new unsent question');assert.equal(store.snapshot().recovery.length,1);
  await store.inspectRequest(request.id);
  assert.equal(store.snapshot().activeId,null);assert.equal(store.snapshot().draft,'new unsent question');assert.equal(store.snapshot().timeline.length,0);assert.equal(store.snapshot().recovery.length,0);
});
test('typing while pending is not discarded by a successful earlier turn',async()=>{
  let complete,body;const store=new LiveChatStore(async(path,options)=>{if(path.startsWith('/v1/chat/sessions?'))return page;body=options.body;return await new Promise(resolve=>{complete=resolve;});});
  store.setDraft('sent question');const pending=store.send('retrieve');store.setDraft('typed next question');complete(reply(body));await pending;
  assert.equal(store.snapshot().draft,'typed next question');assert.equal(store.snapshot().timeline[0].fullText,'sent question');
});
test('history previews retain full-record access without caching every full receipt',async()=>{
  const id='9007199254740993';const full={session_id:sid,id,role:'assistant',provenance_complete:true,text_preview:'x'.repeat(12000),full_text_field:'receipt.answer',receipt:{answer:'x'.repeat(20000),mode:'evidence-extract',citations:[]}};
  const store=new LiveChatStore(async path=>path.includes('/messages?')?{session_id:sid,items:[{id,role:'assistant'}],has_more:false,next_before_id:null}:full);
  await store.select(sid);assert.equal(store.snapshot().timeline[0].fullText.length,4000);assert.equal(store.snapshot().timeline[0].originalLength,20000);
  await store.loadMessage(id);assert.equal(store.snapshot().selected.fullText.length,20000);
});
test('failed transport retains draft and uncertainty, without a fabricated assistant bubble',async()=>{
  const store=new LiveChatStore(async()=>{throw new Error('unavailable');});store.setDraft('keep original');await store.send('generate');
  assert.equal(store.snapshot().draft,'keep original');assert.equal(store.snapshot().timeline.length,0);assert.equal(store.snapshot().recovery.length,1);assert.equal(store.snapshot().pending,false);
  store.reset();assert.equal(store.snapshot().recovery.length,0);assert.equal(store.snapshot().draft,'');
});
test('unsent scratch drafts and their source scopes remain reachable after switching conversations',async()=>{
  const store=new LiveChatStore(async()=>page);store.setDraft('unsent private question');store.chooseSource(source,'1');
  const key=store.key;await store.select(null);store.setDraft('other unsent question');
  assert.equal(store.snapshot().unsentDrafts.find(row=>row.key===key).preview,'unsent private question');
  await store.resumeDraft(key);assert.equal(store.snapshot().draft,'unsent private question');assert.equal(store.snapshot().scope.ids,source);assert.equal(store.snapshot().scope.revision,'1');
});
