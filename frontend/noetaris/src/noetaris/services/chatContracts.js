import { sourceId } from './libraryContracts.js';
export const sessionId = sourceId;
export const messageId = value => typeof value === 'string' && /^[1-9][0-9]{0,18}$/.test(value) && BigInt(value) <= 9223372036854775807n;
export const libraryScope = () => ({ kind:'library',ids:'',revision:'',pages:'' });
export function questionRequest(question,scope,session,request) {
  if(typeof question!=='string'||!question.trim()||Array.from(question).length>1000)throw new Error('Enter a question of 1–1,000 characters. Your draft is retained.');
  if(session!==null&&!sessionId(session))throw new Error('Invalid canonical conversation');
  if(!sessionId(request))throw new Error('Invalid request identity');
  let ids=[],revision=null,pages=[];
  if(scope.kind==='sources'){
    ids=[...new Set(scope.ids.split(',').map(value=>value.trim()).filter(Boolean))];
    if(!ids.length||ids.length>20||!ids.every(sourceId))throw new Error('Select 1–20 exact source IDs; use library scope to search the full indexed library.');
    revision=scope.revision===''?null:scope.revision;
    if(revision!==null&&revision.length>50)throw new Error('Revision exceeds 50 characters.');
    if(scope.pages.trim()){
      const entries=scope.pages.split(',').map(value=>value.trim());
      if(!entries.every(value=>/^\d+$/.test(value)&&Number(value)>=1&&Number(value)<=1000))throw new Error('Pages must be explicit integers from 1–1,000.');
      pages=[...new Set(entries.map(Number))];if(pages.length>100)throw new Error('Select at most 100 pages.');
    }
  }else if(scope.kind!=='library')throw new Error('Unsupported question scope');
  return {question,session_id:session,request_id:request,document_ids:ids.sort(),revision,pages:pages.sort((a,b)=>a-b)};
}
export function chatResult(value,request) {
  if(!value||!sessionId(value.session_id)||typeof value.answer!=='string'||!['evidence-extract','model_unverified'].includes(value.mode)||value.answer_verified!==false||value.provenance_complete!==true||
      !Array.isArray(value.citations)||value.citations.length>100||!Array.isArray(value.source_dependencies)||value.source_dependencies.length>1000||!value.source_dependencies.every(sourceId)||
      value.citations.some(c=>!sourceId(c.document_id)||typeof c.locator!=='string'||typeof c.revision!=='string'||!(/^[a-f0-9]{64}$/).test(c.original_sha256||'')))throw new Error('Unrecognized source-grounded response. Inspect the retained request receipt.');
  if(request){
    const scope=value.memory?.source_scope;
    if(request.session_id!==null&&value.session_id!==request.session_id)throw new Error('Conversation identity changed.');
    if(!scope||JSON.stringify(scope.document_ids)!==JSON.stringify(request.document_ids)||scope.revision!==request.revision||JSON.stringify(scope.pages)!==JSON.stringify(request.pages))throw new Error('Response source scope does not match the question.');
    if(request.document_ids.length && (value.source_dependencies.some(id=>!request.document_ids.includes(id)) || value.citations.some(c=>!request.document_ids.includes(c.document_id)||(request.revision!==null&&c.revision!==request.revision)||(request.pages.length&&!request.pages.includes(c.anchor?.page)))))throw new Error('Response includes evidence outside the selected question scope.');
  }
  return value;
}
export function sessionPage(value){
  if(!value||!Array.isArray(value.items)||value.items.length>50||value.items.some(row=>!sessionId(row.id)||typeof row.created_at!=='string')||typeof value.has_more!=='boolean'||!(value.next_cursor===null||typeof value.next_cursor==='string')||value.has_more!==!!value.next_cursor)throw new Error('Unrecognized conversation page');
  return value;
}
export function messagePage(value,session){
  if(!value||value.session_id!==session||!Array.isArray(value.items)||value.items.length>50||value.items.some(row=>!messageId(row.id)||!['user','assistant'].includes(row.role))||typeof value.has_more!=='boolean'||!(value.next_before_id===null||messageId(value.next_before_id))||value.has_more!==!!value.next_before_id)throw new Error('Unrecognized message page');
  return value;
}
export function historyMessage(value,session,id){
  if(!value||value.session_id!==session||value.id!==id||!messageId(id)||!['user','assistant'].includes(value.role)||value.provenance_complete!==true||typeof value.text_preview!=='string'||
    (value.role==='assistant'&&(value.full_text_field!=='receipt.answer'||typeof value.receipt?.answer!=='string'))||(value.role==='user'&&value.full_text_field!=='text_preview'))throw new Error('Full retained message is unavailable or changed.');
  return {...value,fullText:value.role==='assistant'?value.receipt.answer:value.text_preview};
}
