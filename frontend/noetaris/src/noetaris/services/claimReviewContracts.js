import {retainedId,claimChoices} from './learningContracts.js';
import {messageId} from './chatContracts.js';
import {sourceId} from './libraryContracts.js';
export {claimChoices};
const digest=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
const integer=value=>Number.isSafeInteger(value)&&value>=0;
const states=['candidate','verified','contested','rejected','superseded'];
const row=value=>value&&retainedId(value.id)&&sourceId(value.document_id)&&states.includes(value.status)&&integer(value.revision)&&value.revision>0&&['subject','predicate','value','locator','title','source_version','ingested_by','media_type'].every(key=>typeof value[key]==='string')&&digest(value.original_sha256)&&Array.isArray(value.source_ids)&&value.source_ids.length<=1000&&value.source_ids.every(retainedId)&&typeof value.provenance_complete==='boolean';
export function comparison(value,id,offset,actor){
 const target=value?.claim,citation=value?.citation;
 if(!row(target)||target.id!==id||value.context_schema!=='nsai.claim-review-context/1'||!digest(value.context_sha256)||value.provenance_complete!==true||value.source_integrity!=='sha256-matches-original'||typeof value.can_review!=='boolean'||(value.can_review&&(target.ingested_by===actor||['rejected','superseded'].includes(target.status)))||!Array.isArray(value.source_dependencies)||value.source_dependencies.length>1000||!value.source_dependencies.every(retainedId)||!Array.isArray(value.alternatives)||value.alternatives.length>25||value.alternatives.some(other=>!row(other)||other.id===id||other.subject!==target.subject||other.predicate!==target.predicate||['rejected','superseded'].includes(other.status))||new Set(value.alternatives.map(other=>other.id)).size!==value.alternatives.length||!integer(value.total_alternatives)||value.total_alternatives>2000||value.offset!==offset||value.limit!==25||typeof value.limitation!=='string')throw new Error('Unrecognized source-bound review comparison.');
 if(value.alternatives.length!==Math.min(25,Math.max(0,value.total_alternatives-offset))||value.next_offset!==(offset+25<value.total_alternatives?offset+25:null))throw new Error('Incomplete review alternative pagination.');
 if(!citation||citation.chunk_id!==id||citation.document_id!==target.document_id||citation.original_sha256!==target.original_sha256||citation.revision!==target.source_version||citation.locator!==target.locator||typeof citation.excerpt!=='string')throw new Error('Review evidence does not match its original source.');
 if(citation.anchor&&(citation.anchor.document_id!==target.document_id||citation.anchor.original_sha256!==target.original_sha256||citation.anchor.revision!==target.source_version||citation.anchor.selector?.exact!==citation.excerpt))throw new Error('Review quote belongs to a different source.');
 return value;
}
export function eventPage(value,id){
 if(value?.claim_id!==id||value.limit!==25||value.provenance_complete!==true||!Array.isArray(value.source_dependencies)||value.source_dependencies.length>1000||!value.source_dependencies.every(retainedId)||!Array.isArray(value.items)||value.items.length>25||value.items.some(event=>!messageId(event.id)||typeof event.event_type!=='string'||typeof event.actor!=='string'||typeof event.created_at!=='string'||!event.details||typeof event.details!=='object'||Array.isArray(event.details))||typeof value.has_more!=='boolean'||!(value.next_before_id===null||messageId(value.next_before_id))||value.has_more!==!!value.next_before_id||typeof value.limitation!=='string')throw new Error('Unrecognized exact-ID claim event page.');
 if(value.has_more&&(value.items.length!==25||value.next_before_id!==value.items.at(-1).id))throw new Error('Inconsistent event history cursor.');
 if(value.items.some((event,index)=>index>0&&BigInt(value.items[index-1].id)<=BigInt(event.id)))throw new Error('Event history order changed.');
 return value;
}
export function decisionRequest(data,seen,acknowledged,decision,rationale,actor){
 if(!data||data.can_review!==true||data.claim.ingested_by===actor||['rejected','superseded'].includes(data.claim.status)||!['accept','reject','contest'].includes(decision)||!acknowledged)throw new Error('Inspect the current original source and acknowledge the decision scope.');
 if(decision==='accept'&&new Set(seen).size!==data.total_alternatives)throw new Error('Load every alternative page in the current comparison before acceptance.');
 if(typeof rationale!=='string'||!rationale.trim()||Array.from(rationale).length<10||Array.from(rationale).length>2000)throw new Error('Rationale requires 10 to 2,000 characters; the draft is retained.');
 return {decision,expected_revision:data.claim.revision,expected_context:data.context_sha256,rationale};
}
export function decisionReceipt(value,claim,body,total){
 const expected={accept:'verified',reject:'rejected',contest:'contested'}[body.decision];
 if(value?.claim_id!==claim.id||value.state!==expected||value.revision!==body.expected_revision+1||value.context_sha256!==body.expected_context||!integer(value.superseded_count)||value.superseded_count!==(body.decision==='accept'?total:0)||!digest(value.audit_receipt))throw new Error('Claim transition was not confirmed; reload current state.');
 return value;
}
