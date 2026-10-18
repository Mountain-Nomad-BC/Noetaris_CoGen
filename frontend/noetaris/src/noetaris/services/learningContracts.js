import {sourceId} from './libraryContracts.js';
export const retainedId=value=>typeof value==='string'&&/^[A-Za-z0-9_-]{1,128}$/.test(value);
const digest=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
const positive=value=>Number.isSafeInteger(value)&&value>0;
const states=['candidate','reviewed','rejected'];
const claim=row=>row&&retainedId(row.id)&&sourceId(row.document_id)&&['subject','predicate','value','locator'].every(key=>typeof row[key]==='string')&&positive(row.revision)&&['candidate','verified','contested','rejected','superseded'].includes(row.status);
export function claimChoices(value){
 if(!value||!Array.isArray(value.items)||value.items.length>25||!Number.isSafeInteger(value.total)||value.total<0||value.items.some(row=>!claim(row))||typeof value.has_more!=='boolean'||!(value.next_cursor===null||typeof value.next_cursor==='string')||value.has_more!==!!value.next_cursor)throw new Error('Unrecognized attributable claim page.');
 return value;
}
export function proposalPage(value,{own,actor,state}){
 if(!value||value.authority_granted!==false||value.scope!==(own?'own-authorized':'review-authorized')||value.state_filter!==state||value.snapshot!==false||value.limit!==25||!Number.isSafeInteger(value.total)||value.total<0||typeof value.has_more!=='boolean'||!(value.next_cursor===null||typeof value.next_cursor==='string')||value.has_more!==!!value.next_cursor||!Array.isArray(value.items)||value.items.length>25||typeof value.limitation!=='string')throw new Error('Unrecognized authorized proposal page.');
 if(value.items.some(row=>!retainedId(row.id)||typeof row.author!=='string'||(own&&row.author!==actor)||!retainedId(row.source_claim_id)||!positive(row.revision)||!states.includes(row.state)||(state!=='all'&&row.state!==state)||typeof row.reflection!=='string'||typeof row.created_at!=='string'||typeof row.provenance_complete!=='boolean'||!Array.isArray(row.source_ids)||row.source_ids.length>1000||!row.source_ids.every(retainedId)||!claim(row.source_claim)||row.source_claim.id!==row.source_claim_id||!(row.source_claim.original_sha256===null||digest(row.source_claim.original_sha256))))throw new Error('Proposal source or owner binding changed.');
 return value;
}
export function proposalRequest(selected,text){
 if(!claim(selected)||!sourceId(selected.id))throw new Error('Select an attributable source claim.');
 if(typeof text!=='string'||Array.from(text).length<10||Array.from(text).length>2000||!text.trim())throw new Error('Reflection requires 10 to 2,000 characters; your draft is retained.');
 return {source_claim_id:selected.id,reflection:text};
}
export function proposalReceipt(value){
 if(!value||!sourceId(value.id)||!states.includes(value.state)||typeof value.created!=='boolean'||value.authority_granted!==false||(value.created&&!digest(value.audit_receipt)))throw new Error('Proposal submission was not confirmed. Check retained own proposals before retrying.');
 return value;
}
export function reviewRequest(row,actor,approve,rationale){
 if(!row||row.author===actor||row.state!=='candidate'||row.provenance_complete!==true||!row.source_ids.includes(row.source_claim?.document_id)||!digest(row.source_claim?.original_sha256)||!retainedId(row.id)||!positive(row.revision)||typeof approve!=='boolean')throw new Error('Independent review requires a current attributable candidate. Refresh the list.');
 if(typeof rationale!=='string'||Array.from(rationale).length<10||Array.from(rationale).length>2000||!rationale.trim())throw new Error('Enter review rationale of 10 to 2,000 characters.');
 return {expected_revision:row.revision,approve,rationale};
}
export function reviewReceipt(value,row,approve){
 if(value?.id!==row.id||value.state!==(approve?'reviewed':'rejected')||value.revision!==row.revision+1||value.authority_granted!==false||!digest(value.audit_receipt))throw new Error('Review transition was not confirmed. Reload current proposals.');
 return value;
}
