import {retainedId} from './learningContracts.js';
import {messageId} from './chatContracts.js';
export const governedId=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
const states=['candidate','reviewed','rejected'],kinds=['assembly','issues','proposal','extraction'];
const dependencies=value=>Array.isArray(value)&&value.length<=1000&&value.every(retainedId);
const row=value=>value&&governedId(value.id)&&kinds.includes(value.kind)&&states.includes(value.state)&&typeof value.author==='string'&&retainedId(value.document_id)&&governedId(value.source_sha256)&&typeof value.created_at==='string'&&typeof value.provenance_complete==='boolean'&&dependencies(value.source_ids);
export function governedPage(value,{actor,reviewer,kind,state}){
 if(!value||value.authority_granted!==false||value.snapshot!==false||value.scope!==(reviewer?'review-authorized':'own-authorized')||value.limit!==25||value.legacy_offset!==0||value.kind_filter!==kind||value.state_filter!==state||value.ordering!=='created_at-desc/id-asc'||!Number.isSafeInteger(value.total)||value.total<0||typeof value.has_more!=='boolean'||!(value.next_cursor===null||(typeof value.next_cursor==='string'&&value.next_cursor.length>0&&value.next_cursor.length<=512))||value.has_more!==!!value.next_cursor||!Array.isArray(value.items)||value.items.length>25||(value.has_more&&value.items.length!==25)||typeof value.limitation!=='string')throw new Error('Unrecognized authorized governed candidate page.');
 if(value.items.some(item=>!row(item)||(!reviewer&&item.author!==actor)||(kind!=='all'&&item.kind!==kind)||(state!=='all'&&item.state!==state))||new Set(value.items.map(item=>item.id)).size!==value.items.length)throw new Error('Governed candidate identity, owner or filter changed.');
 return value;
}
export function governedDetail(value,id,{actor,reviewer}){
 if(!row(value)||value.id!==id||(!reviewer&&value.author!==actor)||value.authority_granted!==false||typeof value.can_review!=='boolean'||typeof value.source_integrity_matches!=='boolean'||!Object.hasOwn(value,'payload'))throw new Error('Unrecognized governed candidate detail.');
 const source=value.source,review=value.review;
 if(!source||source.id!==value.document_id||typeof source.title!=='string'||typeof source.revision!=='string'||typeof source.media_type!=='string'||!(source.original_sha256===null||typeof source.original_sha256==='string')||(value.source_integrity_matches&&source.original_sha256!==value.source_sha256))throw new Error('Governed candidate source binding changed.');
 if(value.state==='candidate'?review!==null:(!review||!messageId(review.id)||typeof review.actor!=='string'||!review.actor.trim()||review.actor===value.author||review.decision!==value.state||typeof review.rationale!=='string'||typeof review.created_at!=='string'))throw new Error('Governed review history is inconsistent.');
 if(value.can_review&&(!reviewer||value.author===actor||value.state!=='candidate'||review!==null||!value.source_integrity_matches||!value.provenance_complete||!value.source_ids.includes(value.document_id)))throw new Error('Independent review is unavailable for this candidate.');
 return value;
}
export function governedDecision(value,{actor,reviewer,acknowledged,payloadInspected,decision,rationale}){
 if(!value||value.can_review!==true||!reviewer||value.author===actor||value.state!=='candidate'||value.review!==null||acknowledged!==true||payloadInspected!==true||!['reviewed','rejected'].includes(decision))throw new Error('Inspect the original and complete candidate payload before recording an independent decision.');
 if(typeof rationale!=='string'||!rationale.trim()||Array.from(rationale).length<10||Array.from(rationale).length>2000)throw new Error('Rationale requires 10 to 2,000 characters; the draft is retained.');
 return {decision,rationale};
}
export function governedReceipt(value,id,body){
 if(value?.record_id!==id||value.state!==body.decision||value.authority_granted!==false||!governedId(value.audit_receipt))throw new Error('The governed decision was not confirmed. Read current state before deciding again.');
 return value;
}
