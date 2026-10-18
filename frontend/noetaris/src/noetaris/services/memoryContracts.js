import {sessionId,questionRequest,libraryScope} from './chatContracts.js';
import {sourceId} from './libraryContracts.js';
const digest=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
const integer=value=>Number.isSafeInteger(value)&&value>=0;
export function memoryRequest(session,scope){
 if(!sessionId(session))throw new Error('Select an existing canonical conversation.');
 const body=questionRequest('Inspect candidate memory',scope,session,'0'.repeat(32));
 const expected={document_ids:body.document_ids,revision:body.revision,pages:body.pages};
 const params=new URLSearchParams();for(const id of body.document_ids)params.append('document_ids',id);if(body.revision!==null)params.set('revision',body.revision);for(const page of body.pages)params.append('pages',String(page));
 return {path:`/v1/memory/${session}?${params}`,scope:expected};
}
export function memoryLocation(params){
 const kind=params.get('scope')||'library';if(!['library','sources'].includes(kind))throw new Error('Invalid memory source scope.');
 const session=params.get('session');if(session&&!sessionId(session))throw new Error('Invalid canonical conversation.');
 const scope=kind==='sources'?{kind,ids:params.get('sources')||'',revision:params.get('revision')||'',pages:params.get('pages')||''}:libraryScope();
 if(kind==='library'&&['sources','revision','pages'].some(key=>params.has(key)))throw new Error('Source filters require explicit source scope.');
 if(session)memoryRequest(session,scope);return {session,scope};
}
export function memoryUrl(session,scope){
 memoryRequest(session,scope);const params=new URLSearchParams({session});
 if(scope.kind==='sources'){params.set('scope','sources');params.set('sources',scope.ids);if(scope.revision)params.set('revision',scope.revision);if(scope.pages)params.set('pages',scope.pages);}
 return '/app/memory?'+params;
}
export function memoryProjection(value,{session,actor,scope}){
 const plan=value?.plan;
 if(value?.provenance_complete!==true||value.writeback_policy!=='proposal_only'||typeof value.eligible!=='boolean'||!digest(value.receipt_sha256)||!digest(plan?.plan_sha256)||plan.subject_id!==session||plan.actor_id!==actor||plan.writeback_policy!=='proposal_only'||plan.conflict_policy!=='quarantine'||plan.provenance_required!==true||
   value.envelope_max_bytes!==16384||!integer(value.envelope_bytes)||value.envelope_bytes>16384||!integer(value.serialized_bytes)||value.serialized_bytes>value.max_bytes||value.max_bytes!==12000||
   JSON.stringify(value.source_scope?.document_ids)!==JSON.stringify(scope.document_ids)||value.source_scope?.revision!==scope.revision||JSON.stringify(value.source_scope?.pages)!==JSON.stringify(scope.pages))throw new Error('Memory identity, scope or projection policy changed.');
 for(const [key,max] of [['working',8],['canon',12],['reflection',8],['hypotheses',12],['quarantined',12]])if(!Array.isArray(value[key])||value[key].length>max)throw new Error('Unrecognized bounded memory class.');
 if(!['working','canon','reflection','hypotheses'].every(key=>integer(value.omitted?.[key]))||!integer(value.working_support_policy_omissions)||value.claim_selection?.exhaustive_corpus!==false)throw new Error('Memory omissions or selection coverage are unavailable.');
 if(value.working.some(row=>!['user','assistant'].includes(row.role)||typeof row.text!=='string')||
    value.canon.some(row=>row.status!=='verified'||!row.reviewed_by||!digest(row.original_sha256)||!sourceId(row.document_id)||typeof row.locator!=='string'||(scope.document_ids.length&&!scope.document_ids.includes(row.document_id)))||
    value.reflection.some(row=>!['candidate','reviewed'].includes(row.state)||typeof row.reflection!=='string')||
    value.quarantined.some(row=>typeof row.claim_id!=='string'||typeof row.reason!=='string'))throw new Error('Memory records do not retain their declared authority.');
 if(Array.isArray(value.source_dependencies)){if(value.source_dependencies.length>1000||!value.source_dependencies.every(sourceId))throw new Error('Incomplete memory dependencies.');}
 else if(!sourceId(value.source_manifest_id)||!integer(value.source_dependency_count)||value.source_dependency_count>1000)throw new Error('Missing memory dependency inventory.');
 const candidates=value.research_candidates;
 if(candidates&&(candidates.authority_granted!==false||candidates.canon!==false||candidates.state!=='source-observation-candidates'||!Array.isArray(candidates.items)||candidates.items.length>6||candidates.items.some(row=>!digest(row.id)||!sourceId(row.document_id)||!scope.document_ids.includes(row.document_id)||!digest(row.source_sha256)||row.review_required!==true||typeof row.text!=='string'||!integer(row.excerpt_omitted_characters))))throw new Error('Source candidates cannot import canonical authority.');
 if(scope.document_ids.length&&value.working.length)throw new Error('Explicit source inspection unexpectedly includes working conversation.');
 return value;
}
