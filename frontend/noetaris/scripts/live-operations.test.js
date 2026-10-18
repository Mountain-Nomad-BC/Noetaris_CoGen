import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {operationSpecs,operationView} from '../src/noetaris/services/operationContracts.js';
import {deploymentRequest} from '../src/noetaris/services/deploymentOrigin.js';

test('operations retain backend role boundaries',()=>{
  assert.equal(operationSpecs.audit.permission,'review');
  for(const k of ['analytics','observability','governance','settings'])assert.equal(operationSpecs[k].permission,'admin');
  assert.equal(operationSpecs.integrations.path,'/v1/integrations/status');
});
test('owned split-origin deployment uses exact HTTPS destination and credentialed cookies',()=>{
  const settings={VITE_API_ORIGIN:'https://api.owned.example',VITE_APP_ORIGIN:'https://app.owned.example',VITE_DEPLOYMENT_SITE:'owned.example'};
  assert.deepEqual(deploymentRequest('/v1/chat',settings,settings.VITE_APP_ORIGIN),
    {url:'https://api.owned.example/v1/chat',credentials:'include',crossOrigin:true});
  assert.deepEqual(deploymentRequest('/v1/chat'),{url:'/v1/chat',credentials:'same-origin',crossOrigin:false});
  for(const change of [{VITE_API_ORIGIN:'http://api.owned.example'},{VITE_APP_ORIGIN:'https://project.web.app'},
    {VITE_API_ORIGIN:'https://api.owned.example.evil'},{VITE_API_ORIGIN:'https://user:secret@api.owned.example'},
    {VITE_API_ORIGIN:'https://api.owned.example/path'}])
    assert.throws(()=>deploymentRequest('/v1/chat',{...settings,...change},settings.VITE_APP_ORIGIN));
  assert.throws(()=>deploymentRequest('/v1/chat',settings,'https://different.example'));
});
test('model false and unknown observations are never converted into ready',()=>{
  const value={configured:false,reachable:false,model_loaded:false,model:null,provider:'none',reason:'Not configured'};
  const view=operationView('models',value);assert.equal(view.rows[0].value,false);assert.equal(view.rows[3].value,null);
  assert.throws(()=>operationView('models',{...value,model_loaded:true}));
  assert.throws(()=>operationView('models',{...value,reachable:'true'}));
});
test('partial audit visibility stays unknown and hides source-bearing details',()=>{
  const view=operationView('audit',{valid:null,count:1,head_sha256:'a'.repeat(64),visible_row_hashes_valid:true,scope:'authorized-subset',limitation:'Not global continuity',
    items:[{actor:'reviewer',event_type:'observed',created_at:'2026-10-17',sha256:'b'.repeat(64),details:{private:'PRIVATE_SENTINEL'}}]});
  assert.equal(view.rows.find(r=>r.label==='Visible chain continuity').value,null);
  assert.doesNotMatch(JSON.stringify(view),/PRIVATE_SENTINEL/);
});
test('policy projection excludes staged config values and credential fields',()=>{
  const value={central_integration_enabled:false,generated_code_execution:'disabled',policy:{revision:1,inference_enabled:false,daily_call_limit:20,max_output_tokens:256,central_config:{key:'SECRET_SENTINEL'}}};
  assert.doesNotMatch(JSON.stringify(operationView('settings',value)),/SECRET_SENTINEL/);
  assert.throws(()=>operationView('settings',{...value,policy:{...value.policy,revision:NaN}}));
});
test('missing integration or fabricated commissioning cannot pass',()=>{
  const value={schema_version:'integration-setup/1',partners:['evolus','amd','openrouter'].map(provider=>({provider,credential_configured:false,commissioned:false,dispatch_enabled:false,next_step:'Commission',...(provider==='evolus'?{status:'NOT_CONFIGURED',configuration_ready:false,bindings_configured:false,missing:['Bindings']}: {})}))};
  assert.ok(operationView('integrations',value).rows.length>0);
  assert.throws(()=>operationView('integrations',{...value,partners:value.partners.slice(1)}));
  value.partners[0].dispatch_enabled=true;assert.throws(()=>operationView('integrations',value));
});
test('live operation routes no longer render fixture-backed operational pages',()=>{
  const app=fs.readFileSync(new URL('../src/App.jsx',import.meta.url),'utf8');
  for(const kind of Object.keys(operationSpecs))assert.match(app,new RegExp(`<Route path="${kind}" element=\\{mode === "live" \\? <LiveOperationsPage kind="${kind}"`));
  const page=fs.readFileSync(new URL('../src/noetaris/pages/app/LiveOperationsPage.jsx',import.meta.url),'utf8');
  assert.match(page,/apiRequest\(spec.path/);assert.match(page,/controller.abort\(\)/);assert.match(page,/current=false/);
  assert.doesNotMatch(page,/data\/fixtures|localStorage|sessionStorage|dangerouslySetInnerHTML/);
});

test('developer screen projects live capabilities while excluding identity and secret extras',()=>{
 const value={identity:{token:'PRIVATE_SENTINEL'},indexing:{configured:true},ingestion:'Stored originals',retrieval:'Semantic fusion',learning:'Reviewed proposals',items:[{id:'execution',state:'disabled',limitations:'No admitted executor',routes:['/v1/execute'],authority_granted:false,secret:'PRIVATE_SENTINEL'}]};
 const view=operationView('developers',value);assert.ok(view.rows.some(r=>r.label==='execution state'&&r.value==='disabled'));assert.doesNotMatch(JSON.stringify(view),/PRIVATE_SENTINEL/);
 assert.throws(()=>operationView('developers',{...value,items:[{...value.items[0],authority_granted:true}]}));
});
