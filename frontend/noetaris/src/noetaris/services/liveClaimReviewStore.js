import {apiRequest} from './liveTransport.js';
import {retainedId} from './learningContracts.js';
import {comparison,eventPage,decisionRequest,decisionReceipt} from './claimReviewContracts.js';
const initial=()=>({activeId:null,data:null,context:null,seen:[],acknowledged:false,loading:false,error:null,events:null,eventError:null,eventLoading:false,busy:false,outcome:null,archives:[],notes:Object.create(null)});
export class LiveClaimReviewStore{
 constructor(api=apiRequest){this.api=api;this.state=initial();this.listeners=new Set();this.view=0;this.detailVersion=0;this.eventVersion=0;this.identity=0;this.read=null;this.eventRead=null;this.write=null;}
 snapshot=()=>this.state;subscribe=fn=>{this.listeners.add(fn);return()=>this.listeners.delete(fn);};set=patch=>{this.state={...this.state,...patch};for(const fn of this.listeners)fn();};
 leave=()=>{this.view++;this.detailVersion++;this.eventVersion++;this.read?.abort();this.eventRead?.abort();this.set({data:null,context:null,seen:[],acknowledged:false,events:null,loading:false,eventLoading:false});};
 reset=()=>{this.identity++;this.view++;this.detailVersion++;this.eventVersion++;this.read?.abort();this.eventRead?.abort();this.write?.abort();this.state=initial();for(const fn of this.listeners)fn();};
 note=(id,text)=>{if(!Object.hasOwn(this.state.notes,id)&&Object.keys(this.state.notes).length>=100){this.set({error:'Clear an existing rationale draft before retaining more than 100.'});return;}const notes=Object.assign(Object.create(null),this.state.notes);if(text)notes[id]=text;else delete notes[id];this.set({notes});};
 acknowledge=value=>this.set({acknowledged:value===true});
 open=async(id,actor)=>{this.leave();this.set({activeId:id,error:null,eventError:null});if(id)await Promise.all([this.load(id,0,actor,true),this.loadEvents(id)]);};
 observe(attempt,data){return attempt?.status==='uncertain'&&attempt.claim.id===data.claim.id?{...attempt,status:'observed',observed:{id:data.claim.id,state:data.claim.status,revision:data.claim.revision}}:attempt;}
 load=async(id,offset,actor,reset=false)=>{
  if(!retainedId(id)){this.set({error:'Invalid claim identifier'});return;}
  const view=this.view,version=++this.detailVersion;this.read?.abort();this.read=new AbortController();const baseline=reset?null:this.state.context,prior=reset?[]:this.state.seen;
  this.set({loading:true,data:null,error:null,...(reset?{context:null,seen:[],acknowledged:false}:{})});
  try{const data=comparison(await this.api('/v1/claims/'+encodeURIComponent(id)+'?offset='+offset,{signal:this.read.signal}),id,offset,actor);if(view!==this.view||version!==this.detailVersion||this.state.activeId!==id)return;
   if(baseline&&baseline!==data.context_sha256)throw new Error('Comparison changed. Reload from the first page and inspect the new scope.');
   const seen=[...new Set([...prior,...data.alternatives.map(row=>row.id)])];if(seen.length>data.total_alternatives)throw new Error('Comparison coverage is inconsistent. Reload current state.');
   this.set({loading:false,data,context:data.context_sha256,seen,outcome:this.observe(this.state.outcome,data),archives:this.state.archives.map(attempt=>this.observe(attempt,data))});
  }catch(error){if(view===this.view&&version===this.detailVersion&&error.name!=='AbortError')this.set({loading:false,data:null,context:null,seen:[],acknowledged:false,error:error.message});}
 };
 loadEvents=async(id,before=null)=>{const view=this.view,version=++this.eventVersion;this.eventRead?.abort();this.eventRead=new AbortController();this.set({eventLoading:true,events:null,eventError:null});
  try{const data=eventPage(await this.api('/v1/claims/'+encodeURIComponent(id)+'/events'+(before?'?before_id='+encodeURIComponent(before):''),{signal:this.eventRead.signal}),id);if(view===this.view&&version===this.eventVersion&&this.state.activeId===id)this.set({events:data,eventLoading:false});}
  catch(error){if(view===this.view&&version===this.eventVersion&&error.name!=='AbortError')this.set({events:null,eventLoading:false,eventError:error.message});}
 };
 decide=async(decision,actor)=>{
  if(this.state.busy||this.state.outcome?.status==='uncertain')return;
  const claim=this.state.data?.claim,total=this.state.data?.total_alternatives;let body;try{body=decisionRequest(this.state.data,this.state.seen,this.state.acknowledged,decision,this.state.notes[claim?.id]||'',actor);}catch(error){this.set({error:error.message});return;}
  const identity=this.identity;this.write=new AbortController();this.set({busy:true,error:null,outcome:{status:'pending',claim:{id:claim.id,revision:claim.revision},body},data:null,context:null,seen:[],acknowledged:false});
  this.detailVersion++;this.read?.abort();
  try{const receipt=decisionReceipt(await this.api('/v1/review/'+encodeURIComponent(claim.id),{method:'POST',body,signal:this.write.signal}),claim,body,total);if(identity!==this.identity)return;
   this.set({busy:false,outcome:{status:'confirmed',claim:{id:claim.id,revision:claim.revision},body,receipt}});
   if(this.state.activeId===claim.id)await Promise.all([this.load(claim.id,0,actor,true),this.loadEvents(claim.id)]);
  }catch(error){if(identity===this.identity){const rejected=Number.isInteger(error.status)&&error.status>=400&&error.status<500;this.set({busy:false,outcome:{status:rejected?'rejected':'uncertain',claim:{id:claim.id,revision:claim.revision},body},data:null,context:null,seen:[],acknowledged:false,error:error.message});}}
 };
 archive=()=>{if(this.state.outcome?.status!=='uncertain'||this.state.busy)return;if(this.state.archives.length>=10){this.set({error:'Resolve and clear an archived snapshot before retaining more than 10.'});return;}this.set({archives:[...this.state.archives,this.state.outcome],outcome:null,error:null});};
 clearArchive=index=>{if(this.state.archives[index]?.status!=='uncertain')this.set({archives:this.state.archives.filter((_,position)=>position!==index)});};
}
