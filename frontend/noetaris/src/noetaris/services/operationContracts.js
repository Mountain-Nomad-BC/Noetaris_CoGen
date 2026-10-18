import {usageObservation} from './governanceContracts.js';

export const operationSpecs=Object.freeze({
  developers:{title:'Live API capabilities',permission:'read',path:'/v1/capabilities'},
  models:{title:'Model status',permission:'read',path:'/v1/model/status'},
  integrations:{title:'Integration setup',permission:'read',path:'/v1/integrations/status'},
  analytics:{title:'Measured inference activity',permission:'admin',path:'/v1/admin/resources'},
  observability:{title:'Runtime observations',permission:'admin',path:'/v1/admin/resources'},
  governance:{title:'Security and inference policy',permission:'admin',path:'/v1/admin/security'},
  settings:{title:'Effective deployment settings',permission:'admin',path:'/v1/admin/security'},
  audit:{title:'Authorized audit events',permission:'review',path:'/v1/audit'},
});
const object=v=>v&&typeof v==='object'&&!Array.isArray(v);
const integer=v=>Number.isSafeInteger(v)&&v>=0;
const digest=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
const text=v=>typeof v==='string'&&v.length<=2000;
const bool=v=>typeof v==='boolean';

export function operationView(kind,value){
  if(!operationSpecs[kind]||!object(value))throw new Error('Unrecognized operation response');
  const rows=[];let events=[];let notice='Read-only server observations. Refresh to read current state.';
  const row=(label,value)=>rows.push({label,value});
  if(kind==='developers'){
    if(!Array.isArray(value.items)||value.items.length>100||!object(value.indexing)||!bool(value.indexing.configured)||!text(value.ingestion)||!text(value.retrieval)||!text(value.learning))throw new Error('Unrecognized live capabilities');
    row('Document ingestion',value.ingestion);row('Index worker configured',value.indexing.configured);row('Retrieval',value.retrieval);row('Learning',value.learning);
    for(const item of value.items){
      if(!object(item)||!text(item.id)||!text(item.state)||!text(item.limitations)||item.authority_granted!==false||!Array.isArray(item.routes)||item.routes.length>30||!item.routes.every(route=>text(route)&&route.startsWith('/v1/')))throw new Error('Unrecognized live capability');
      row(item.id+' state',item.state);row(item.id+' routes',item.routes.join(', ')||'No live route');row(item.id+' limits',item.limitations);
    }
    notice='Capabilities declared by the current API. Disabled and partial surfaces remain visible; declarations do not establish independent qualification. No API credentials are displayed.';
  }else if(kind==='models'){
    if(!['configured','reachable','model_loaded'].every(k=>bool(value[k]))||
       !(value.model===null||text(value.model))||!text(value.provider)||
       !(value.reason===null||text(value.reason))||
       (value.model_loaded&&(!value.configured||!value.reachable)))throw new Error('Unrecognized model status');
    for(const k of ['configured','reachable','model_loaded','model','provider','reason'])row(k.replaceAll('_',' '),value[k]);
    notice='Model reachability does not establish answer quality or authorize hosted source export.';
  }else if(kind==='integrations'){
    if(value.schema_version!=='integration-setup/1'||!Array.isArray(value.partners)||value.partners.length!==3||
       new Set(value.partners.map(p=>p.provider)).size!==3)throw new Error('Unrecognized integration setup');
    for(const p of value.partners){
      if(!['amd','evolus','openrouter'].includes(p.provider)||!bool(p.credential_configured)||
         p.commissioned!==false||p.dispatch_enabled!==false||!text(p.next_step))throw new Error('Unrecognized partner state');
      row(p.provider+' credential configured',p.credential_configured);
      row(p.provider+' commissioned',p.commissioned);row(p.provider+' dispatch enabled',p.dispatch_enabled);
      if(p.provider==='evolus'){
        if(!['NOT_CONFIGURED','CONFIGURED_NOT_COMMISSIONED'].includes(p.status)||!bool(p.bindings_configured)||!bool(p.configuration_ready)||!Array.isArray(p.missing)||!p.missing.every(text))throw new Error('Unrecognized Evolus bindings');
        row('Evolus status',p.status);
        row('Evolus bindings configured',p.bindings_configured);row('Evolus configuration ready',p.configuration_ready);
        for(const missing of p.missing)row('Evolus missing',missing);
      }
      row(p.provider+' next step',p.next_step);
    }
    notice='Server-side configuration checks only. No partner request is made by refreshing this page.';
  }else if(kind==='analytics'||kind==='observability'){
    usageObservation(value);
    for(const k of ['period','attempts','completed_inferences','observed_latency_ms','latency_observations',
      'observed_completion_tokens','token_observations','financial_cost','verified_outcome_cost'])row(k.replaceAll('_',' '),value[k]);
    notice='Visible authorized inference records only. Completed inference is not a verified outcome. Unknown measurements remain unknown.';
  }else if(kind==='governance'||kind==='settings'){
    const p=value.policy;
    if(!object(p)||!integer(p.revision)||!bool(p.inference_enabled)||!integer(p.daily_call_limit)||
       !integer(p.max_output_tokens)||!bool(value.central_integration_enabled)||!text(value.generated_code_execution))
      throw new Error('Unrecognized effective policy');
    for(const k of ['revision','inference_enabled','daily_call_limit','max_output_tokens'])row(k.replaceAll('_',' '),p[k]);
    row('Central integration enabled',value.central_integration_enabled);row('Generated code execution',value.generated_code_execution);
    notice='Effective read-only policy. Configuration changes remain governed by the administrator/reviewer API; this screen does not bypass approval.';
  }else if(kind==='audit'){
    if(!(value.valid===null||bool(value.valid))||!integer(value.count)||!digest(value.head_sha256)||
       !bool(value.visible_row_hashes_valid)||!text(value.scope)||!text(value.limitation)||
       !Array.isArray(value.items)||value.items.length>100)throw new Error('Unrecognized audit observation');
    row('Visible event count',value.count);row('Visible row hashes valid',value.visible_row_hashes_valid);
    row('Visible chain continuity',value.valid);row('Scope',value.scope);row('Visible head SHA-256',value.head_sha256);
    events=value.items.map(item=>{
      if(!object(item)||!text(item.actor)||!text(item.event_type)||!text(item.created_at)||!digest(item.sha256))throw new Error('Unrecognized audit event');
      return {actor:item.actor,type:item.event_type,at:item.created_at,digest:item.sha256};
    });
    notice=value.limitation;
  }
  return {rows,events,notice};
}
