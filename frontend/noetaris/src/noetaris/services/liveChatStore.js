import { apiRequest } from './liveTransport.js';
import { sessionId,messageId,libraryScope,questionRequest,chatResult,sessionPage,messagePage,historyMessage } from './chatContracts.js';
const initial = () => ({activeId:null,draft:'',scope:libraryScope(),unsentDrafts:[],sessions:null,sessionCursor:null,messages:null,selected:null,timeline:[],pending:false,loading:false,error:null,notice:null,recovery:[]});
export class LiveChatStore {
  constructor(api=apiRequest){this.api=api;this.state=initial();this.listeners=new Set();this.controllers=new Set();this.epoch=0;this.sessionEpoch=0;this.drafts=new Map();this.key='draft-'+crypto.randomUUID();}
  snapshot=()=>this.state;
  subscribe=fn=>{this.listeners.add(fn);return()=>this.listeners.delete(fn);};
  set=patch=>{this.state={...this.state,...patch,unsentDrafts:[...this.drafts].map(([key,value])=>({key,preview:value.text.slice(0,60)}))};for(const fn of this.listeners)fn();};
  reset=()=>{this.epoch++;this.sessionEpoch++;for(const controller of this.controllers)controller.abort();this.controllers.clear();this.drafts.clear();this.key='draft-'+crypto.randomUUID();this.state=initial();for(const fn of this.listeners)fn();};
  async request(path,options={}){const controller=new AbortController();this.controllers.add(controller);try{return await this.api(path,{...options,signal:controller.signal});}finally{this.controllers.delete(controller);}}
  cancel=()=>{this.epoch++;for(const controller of this.controllers)controller.abort();this.controllers.clear();this.set({pending:false,loading:false,notice:'Browser request cancelled. Server execution may have completed; inspect its receipt before retrying.'});};
  setDraft=value=>this.set({draft:value});
  changeScope=patch=>{this.cancel();this.set({scope:{...this.state.scope,...patch},selected:null,error:null,notice:'Question scope changed explicitly. Earlier answers are retained in history.'});};
  chooseSource=(id,revision)=>{if(!sessionId(id))throw new Error('Invalid source');this.changeScope({kind:'sources',ids:id,revision,pages:''});};
  rememberDraft(){if(this.state.draft)this.drafts.set(this.key,{text:this.state.draft,scope:{...this.state.scope}});else this.drafts.delete(this.key);}
  async loadSessions(cursor=null){const version=++this.sessionEpoch;const root=this.epoch;try{const data=sessionPage(await this.request('/v1/chat/sessions?'+new URLSearchParams({limit:'25',...(cursor?{cursor}:{})})));if(root===this.epoch&&version===this.sessionEpoch)this.set({sessions:data,sessionCursor:cursor});}catch(error){if(root===this.epoch&&error.name!=='AbortError')this.set({error:error.message});}}
  select=async id=>{
    if(id!==null&&!sessionId(id)){this.set({error:'Invalid conversation identifier'});return;}
    if(this.drafts.size>=50&&!this.drafts.has(id)&&this.state.draft){this.set({error:'Save or send an existing unsent draft before opening more conversations.'});return;}
    this.rememberDraft();this.cancel();this.key=id||'draft-'+crypto.randomUUID();
    const saved=this.drafts.get(this.key);
    this.set({activeId:id,draft:saved?.text||'',scope:saved?.scope||libraryScope(),messages:null,selected:null,timeline:[],error:null,notice:saved?'Resumed the tab draft and its explicit source scope.':'New question scope: entire authorized indexed library.'});
    if(id)await this.loadMessages(null);
  };
  resumeDraft=async key=>{
    if(!this.drafts.has(key)){this.set({error:'Unsent tab draft is unavailable'});return;}
    if(sessionId(key)){await this.select(key);return;}
    if(this.drafts.size>=50&&!this.drafts.has(this.key)&&this.state.draft){this.set({error:'Submit or save the current draft before opening another.'});return;}
    this.rememberDraft();this.cancel();this.key=key;const saved=this.drafts.get(key);
    this.set({activeId:null,draft:saved.text,scope:saved.scope,messages:null,selected:null,timeline:[],error:null,notice:'Resumed the unsent tab draft and its explicit source scope.'});
  };
  loadMessages=async before=>{
    if(!this.state.activeId)return;const id=this.state.activeId;this.cancel();const version=this.epoch;
    this.set({loading:true,messages:null,selected:null,timeline:[],error:null,notice:null});
    try{
      const page=messagePage(await this.request(`/v1/chat/sessions/${id}/messages?`+new URLSearchParams({limit:'20',...(before?{before_id:before}:{})})),id);
      if(version!==this.epoch)return;this.set({messages:page});
      const loaded=new Array(page.items.length);let next=0;
      const worker=async()=>{
        while(version===this.epoch){const index=next++;if(index>=page.items.length)return;const item=page.items[index];
          try{
            const record=historyMessage(await this.request(`/v1/chat/sessions/${id}/messages/${item.id}`),id,item.id);
            const receipt=record.receipt;
            loaded[index]={id:item.id,role:record.role,fullText:record.fullText.slice(0,4000),originalLength:record.fullText.length,previewOnly:record.fullText.length>4000,
              receipt:record.role==='assistant'?{mode:receipt.mode,citations:receipt.citations,answer_verified:receipt.answer_verified,memory:{source_scope:receipt.memory?.source_scope},source_dependencies:receipt.source_dependencies,support_validation:receipt.support_validation,run_id:receipt.run_id,audit_receipt:receipt.audit_receipt}:null};
          }catch(error){if(version===this.epoch&&error.name!=='AbortError')loaded[index]={id:item.id,role:item.role,unavailable:true,error:error.message};}
        }
      };
      await Promise.all([worker(),worker()]);
      if(version===this.epoch)this.set({timeline:loaded.filter(Boolean).reverse(),loading:false});
    }catch(error){if(version===this.epoch&&error.name!=='AbortError')this.set({loading:false,error:error.message});}
  };
  loadMessage=async message=>{
    if(!messageId(message)){this.set({error:'Invalid exact message identifier'});return;}
    const id=this.state.activeId;if(!id)return;this.cancel();const version=this.epoch;this.set({loading:true,selected:null,error:null,notice:null});
    try{const record=historyMessage(await this.request(`/v1/chat/sessions/${id}/messages/${message}`),id,message);if(version===this.epoch)this.set({selected:record,loading:false});}
    catch(error){if(version===this.epoch&&error.name!=='AbortError')this.set({loading:false,error:error.message});}
  };
  send=async mode=>{
    if(this.state.pending)return;
    if(!['retrieve','generate'].includes(mode)){this.set({error:'Unsupported conversation operation'});return;}
    if(this.state.recovery.length>=10){this.set({error:'Inspect unresolved request receipts before submitting more work.'});return;}
    let body;
    try{body=questionRequest(this.state.draft,this.state.scope,this.state.activeId,crypto.randomUUID().replaceAll('-',''));}
    catch(error){this.set({error:error.message});return;}
    this.cancel();const version=this.epoch;const key=this.key;
    const record={id:body.request_id,body,mode,key};
    this.set({pending:true,selected:null,error:null,notice:null,recovery:[...this.state.recovery,record]});
    try{
      const reply=chatResult(await this.request(mode==='generate'?'/v1/reason':'/v1/chat',{method:'POST',body}),body);
      if(version!==this.epoch||key!==this.key)return;
      const draft=this.state.draft===body.question?'':this.state.draft;
      this.drafts.delete(key);this.key=reply.session_id;
      const timeline=[...this.state.timeline,{id:'question-'+record.id,role:'user',fullText:body.question,receipt:null},{id:'answer-'+record.id,role:'assistant',fullText:reply.answer,receipt:reply}].slice(-20);
      this.set({activeId:reply.session_id,draft,pending:false,selected:null,timeline,messages:null,recovery:this.state.recovery.filter(item=>item.id!==record.id),notice:'Server response retained. Load history to inspect other records; generated explanations remain unverified.'});
      this.loadSessions(this.state.sessionCursor);
    }catch(error){if(version===this.epoch&&error.name!=='AbortError')this.set({pending:false,error:error.message,notice:'No completion was received. Draft retained; inspect the request receipt before retrying.'});}
  };
  inspectRequest=async id=>{
    const item=this.state.recovery.find(row=>row.id===id);if(!item)return;
    const version=this.epoch;
    try{
      const receipt=await this.request('/v1/invocations/'+id);if(version!==this.epoch)return;
      if(receipt.state==='completed'&&receipt.response){
        const reply=chatResult(receipt.response,item.body);
        this.set({recovery:this.state.recovery.filter(row=>row.id!==id),notice:`Completed response retained in conversation ${reply.session_id}. Select that conversation to view it.`});
        await this.loadSessions(null);
      }else if(receipt.state==='failed')this.set({recovery:this.state.recovery.filter(row=>row.id!==id),notice:'Request is terminally failed. Inspect history before explicitly submitting a new question.'});
      else this.set({notice:receipt.response_withheld||'Request remains pending. No automatic retry or duplicate generation was submitted.'});
    }catch(error){if(version===this.epoch&&error.name!=='AbortError')this.set({error:error.message});}
  };
}
