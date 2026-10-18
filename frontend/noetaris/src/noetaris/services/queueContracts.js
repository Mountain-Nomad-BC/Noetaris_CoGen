import {sourceId} from './libraryContracts.js';
const hash=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
const count=value=>Number.isSafeInteger(value)&&value>=0;
export function indexSnapshot(value,id){
 if(!sourceId(id)||!value||value.document_id!==id||!['queued','running','ready','failed','cancelled','not-commissioned'].includes(value.state)||typeof value.ready!=='boolean')throw new Error('Unrecognized source-bound indexing status.');
 if(value.state==='not-commissioned'){if(value.ready)throw new Error('Uncommissioned source cannot be ready.');return value;}
 if(!['queued','running','succeeded','failed','cancelled'].includes(value.job_state)||!Number.isInteger(value.priority)||value.priority<0||value.priority>9||!count(value.epoch)||value.epoch<1||!count(value.attempts)||!(value.job_id===null||hash(value.job_id))||!(value.publication_id===null||hash(value.publication_id))||!(value.error_code===null||typeof value.error_code==='string')||!['passages_total','passages_completed'].every(key=>value[key]===null||count(value[key]))||!(value.source_coverage_complete===null||typeof value.source_coverage_complete==='boolean')||(value.passages_total!==null&&value.passages_completed!==null&&value.passages_completed>value.passages_total)||(value.ready&&!hash(value.publication_id)))throw new Error('Indexing status has invalid revision or progress fields.');
 return value;
}
export function retryRequest(snapshot,source,identity){
 indexSnapshot(snapshot,source?.id);
 if(identity?.identity_kind!=='local-user'||!identity.permissions?.includes('ingest')||source.can_manage_access!==true||!['failed','cancelled'].includes(snapshot.job_state)||!hash(snapshot.job_id))throw new Error('Retry requires current failed state and an authorized individual source owner.');
 return {expected_epoch:snapshot.epoch};
}
export function retryReceipt(value,snapshot){if(value?.state!=='queued'||value.job_id!==snapshot.job_id)throw new Error('Retry was not confirmed for the exact indexing job.');return value;}

export function controlRequest(snapshot,source,identity,action,priority){
 indexSnapshot(snapshot,source?.id);
 if(identity?.identity_kind!=='local-user'||!identity.permissions?.includes('ingest')||source.can_manage_access!==true||!hash(snapshot.job_id))throw new Error('Queue changes require current individual source ownership and ingestion permission.');
 if(action==='cancel'&&['queued','running'].includes(snapshot.job_state))return {expected_epoch:snapshot.epoch};
 if(action==='priority'&&snapshot.job_state==='queued'&&/^[0-9]$/.test(String(priority)))return {expected_epoch:snapshot.epoch,priority:Number(priority)};
 throw new Error('Queue control does not match the current job state or supported priority range0 through9.');
}
export function controlReceipt(value,snapshot,action,body){
 if(!value||value.document_id!==snapshot.document_id||value.job_id!==snapshot.job_id||value.epoch!==body.expected_epoch+1||!count(value.epoch)||!hash(value.audit_receipt)||
    (action==='cancel'&&(value.state!=='cancelled'||!['ready','cancelled'].includes(value.index_state)))||
    (action==='priority'&&(value.state!=='queued'||value.priority!==body.priority))||!['cancel','priority'].includes(action))throw new Error('Queue control was not confirmed for the exact source, job and version.');
 return value;
}
