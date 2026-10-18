import {apiRequest} from './liveTransport.js';
import {governedId,governedDetail,governedDecision,governedReceipt} from './governedContracts.js';
const initial=()=>({activeId:null,data:null,loading:false,error:null,acknowledged:false,payloadInspected:false,busy:false,outcome:null,archives:[],notes:Object.create(null)});
export class LiveGovernedStore{
 constructor(api=apiRequest){this.api=api;this.state=initial();this.listeners=new Set();this.view=0;this.version=0;this.identity=0;this.read=null;this.write=null;}
 snapshot=()=>this.state;subscribe=fn=>{this.listeners.add(fn);return()=>this.listeners.delete(fn);};set=patch=>{this.state={...this.state,...patch};for(const fn of this.listeners)fn();};
 leave=()=>{this.view++;this.version++;this.read?.abort();this.set({data:null,loading:false,acknowledged:false,payloadInspected:false});};
 reset=()=>{this.identity++;this.view++;this.version++;this.read?.abort();this.write?.abort();this.state=initial();for(const fn of this.listeners)fn();};
 note=(id,text)=>{if(!Object.hasOwn(this.state.notes,id)&&Object.keys(this.state.notes).length>=100){this.set({error:'Clear an existing rationale draft before retaining more than 100.'});return;}const notes=Object.assign(Object.create(null),this.state.notes);if(text)notes[id]=text;else delete notes[id];this.set({notes});};
 acknowledge=value=>this.set({acknowledged:value===true});
 inspectPayload=()=>{if(this.state.data)this.set({payloadInspected:true});};
 open=async(id,principal)=>{this.leave();this.set({activeId:id,error:null});if(id)await this.load(id,principal);};
 observe=(attempt,value)=>attempt?.status==='uncertain'&&attempt.record.id===value.id?{...attempt,status:'observed',observed:{id:value.id,state:value.state,review_id:value.review?.id||null}}:attempt;
 load=async(id,principal)=>{
  if(!governedId(id)){this.set({error:'Invalid governed candidate identity'});return;}
  const view=this.view,version=++this.version;this.read?.abort();this.read=new AbortController();this.set({loading:true,data:null,error:null,acknowledged:false,payloadInspected:false});
  try{const data=governedDetail(await this.api('/v1/governed/records/'+encodeURIComponent(id),{signal:this.read.signal}),id,principal);if(view!==this.view||version!==this.version||this.state.activeId!==id)return;this.set({loading:false,data,outcome:this.observe(this.state.outcome,data),archives:this.state.archives.map(attempt=>this.observe(attempt,data))});}
  catch(error){if(view===this.view&&version===this.version&&error.name!=='AbortError')this.set({loading:false,data:null,error:error.message,acknowledged:false});}
 };
 decide=async(decision,principal)=>{
  if(this.state.busy||this.state.outcome?.status==='uncertain')return;
  const record=this.state.data;let body;
  try{body=governedDecision(record,{...principal,acknowledged:this.state.acknowledged,payloadInspected:this.state.payloadInspected,decision,rationale:this.state.notes[record?.id]||''});}catch(error){this.set({error:error.message});return;}
  const identity=this.identity;this.write=new AbortController();this.version++;this.read?.abort();this.set({busy:true,data:null,acknowledged:false,payloadInspected:false,error:null,outcome:{status:'pending',record:{id:record.id},body}});
  try{const receipt=governedReceipt(await this.api('/v1/governed/records/'+encodeURIComponent(record.id)+'/review',{method:'POST',body,signal:this.write.signal}),record.id,body);if(identity!==this.identity)return;this.set({busy:false,outcome:{status:'confirmed',record:{id:record.id},body,receipt}});if(this.state.activeId===record.id)await this.load(record.id,principal);}
  catch(error){if(identity===this.identity)this.set({busy:false,data:null,acknowledged:false,error:error.message,outcome:{status:'uncertain',record:{id:record.id},body}});}
 };
 archive=()=>{if(this.state.outcome?.status!=='uncertain'||this.state.busy)return;if(this.state.archives.length>=10){this.set({error:'Resolve and explicitly clear an archived snapshot before retaining more than 10.'});return;}this.set({archives:[...this.state.archives,this.state.outcome],outcome:null,error:null});};
 clearArchive=index=>{if(this.state.archives[index]?.status!=='uncertain')this.set({archives:this.state.archives.filter((_,position)=>position!==index)});};
}
