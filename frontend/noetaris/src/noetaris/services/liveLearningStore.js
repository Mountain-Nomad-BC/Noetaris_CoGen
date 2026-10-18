import {apiRequest} from './liveTransport.js';
import {proposalRequest,proposalReceipt,reviewRequest,reviewReceipt} from './learningContracts.js';
const initial=()=>({draft:'',claim:null,busy:false,outcome:null,error:null,reviewNotes:Object.create(null),archives:[]});
export class LiveLearningStore{
 constructor(api=apiRequest){this.api=api;this.state=initial();this.listeners=new Set();this.epoch=0;this.controller=null;}
 snapshot=()=>this.state;subscribe=fn=>{this.listeners.add(fn);return()=>this.listeners.delete(fn);};
 set=patch=>{this.state={...this.state,...patch};for(const fn of this.listeners)fn();};
 reset=()=>{this.epoch++;this.controller?.abort();this.controller=null;this.state=initial();for(const fn of this.listeners)fn();};
 setDraft=text=>this.set({draft:text});
 setReviewNote=(id,text)=>{if(!Object.hasOwn(this.state.reviewNotes,id)&&Object.keys(this.state.reviewNotes).length>=100){this.set({error:'Clear an existing review draft before opening more than 100.'});return;}const notes=Object.assign(Object.create(null),this.state.reviewNotes);if(text)notes[id]=text;else delete notes[id];this.set({reviewNotes:notes});};
 choose=claim=>{if(!this.state.busy)this.set({claim,error:null});};
 clear=()=>{if(!this.state.busy&&this.state.outcome?.status!=='uncertain')this.set({draft:'',claim:null,error:null});};
 submit=async()=>{
  if(this.state.busy||this.state.outcome?.status==='uncertain')return;
  let body;try{body=proposalRequest(this.state.claim,this.state.draft);}catch(error){this.set({error:error.message});return;}
  const version=++this.epoch;this.controller=new AbortController();this.set({busy:true,error:null,outcome:{kind:'create',status:'pending',body}});
  try{const receipt=proposalReceipt(await this.api('/v1/learning',{method:'POST',body,signal:this.controller.signal}));if(version===this.epoch)this.set({busy:false,outcome:{kind:'create',status:'confirmed',body,receipt},error:null});}
  catch(error){if(version===this.epoch){const rejected=Number.isInteger(error.status)&&error.status>=400&&error.status<500;this.set({busy:false,outcome:{kind:'create',status:rejected?'rejected':'uncertain',body},error:error.message});}}
 };
 review=async(row,actor,approve)=>{
  if(this.state.busy||this.state.outcome?.status==='uncertain')return;
  let body;try{body=reviewRequest(row,actor,approve,this.state.reviewNotes[row.id]||'');}catch(error){this.set({error:error.message});return;}
  const version=++this.epoch;this.controller=new AbortController();const attempt={kind:'review',row,body};this.set({busy:true,error:null,outcome:{...attempt,status:'pending'}});
  try{const receipt=reviewReceipt(await this.api(`/v1/learning/${encodeURIComponent(row.id)}/review`,{method:'POST',body,signal:this.controller.signal}),row,approve);if(version===this.epoch)this.set({busy:false,outcome:{...attempt,status:'confirmed',receipt},error:null});}
  catch(error){if(version===this.epoch){const rejected=Number.isInteger(error.status)&&error.status>=400&&error.status<500;this.set({busy:false,outcome:{...attempt,status:rejected?'rejected':'uncertain'},error:error.message});}}
 };
 archiveUncertain=()=>{
  if(this.state.busy||this.state.outcome?.status!=='uncertain')return;
  if(this.state.archives.length>=10){this.set({error:'Resolve and clear an archived attempt before retaining more than 10 uncertain write snapshots.'});return;}
  this.set({archives:[...this.state.archives,this.state.outcome],outcome:null,error:null});
 };
 clearArchive=index=>{if(this.state.archives[index]?.status==='uncertain')return;this.set({archives:this.state.archives.filter((_,position)=>position!==index)});};
 recovered(attempt,items){
  if(attempt?.status!=='uncertain')return attempt;
  if(attempt.kind==='review'){
   const found=items.find(row=>row.id===attempt.row.id);
   return found?{...attempt,status:'reconciled',observed:{id:found.id,revision:found.revision,state:found.state}}:attempt;
  }
  const body=attempt.body,found=items.find(row=>row.source_claim_id===body.source_claim_id&&row.reflection===body.reflection);
  return found?{kind:'create',status:'confirmed',body,receipt:{id:found.id,state:found.state,created:false,authority_granted:false},recovered:true}:attempt;
 }
 reconcile=items=>{
  const outcome=this.recovered(this.state.outcome,items),archives=this.state.archives.map(attempt=>this.recovered(attempt,items));
  if(outcome!==this.state.outcome||archives.some((attempt,index)=>attempt!==this.state.archives[index]))this.set({outcome,archives,error:null});
 };
}
