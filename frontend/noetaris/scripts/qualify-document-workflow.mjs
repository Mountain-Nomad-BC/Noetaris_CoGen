import fs from 'node:fs';import crypto from 'node:crypto';import {createRequire} from 'node:module';import {fileURLToPath} from 'node:url';
import {documentFixture} from './documentFixtures.mjs';
const root=new URL('../../../',import.meta.url);process.chdir(fileURLToPath(root));
const require=createRequire(new URL('../package.json',import.meta.url));const {chromium}=require('playwright');
const kind=process.env.NSAI_UPLOAD_KIND||'markdown';const isPdf=kind==='pdf';const isCsv=kind==='csv';const id=crypto.randomUUID();const identity=fs.readFileSync(new URL('state/integration/identity.json',root),'utf8');
const currentIdentity=JSON.parse(identity);if(currentIdentity.project!=='noetaris-integration'||currentIdentity.release_admitted!==false||currentIdentity.scope!=='synthetic integration only')throw new Error('Owned synthetic integration required');
const report={run_id:id,identity:JSON.parse(identity),producer_sha256:crypto.createHash('sha256').update(fs.readFileSync(new URL(import.meta.url))).digest('hex'),scope:'Real browser upload, automatic indexing, graph and source-scoped query on owned synthetic Docker; no mocked responses',checks:[],errors:[],responses:[]};
const width=process.env.NSAI_BROWSER_WIDTH==='390'?390:1440;report.viewport_width=width;const browser=await chromium.launch({headless:true});const page=await browser.newPage({viewport:{width,height:1100}});page.setDefaultTimeout(30000);
const check=(name,value)=>{report.checks.push({name,passed:!!value});console.log(JSON.stringify({check:name,passed:!!value}));if(!value)throw new Error(name);};
const library=async()=>{await page.getByTestId('app-shell').waitFor();await page.waitForLoadState('networkidle');const menu=page.getByTestId('topbar-menu-btn');if(width<768){await menu.click();await page.getByTestId('sidebar-backdrop').waitFor();}await page.locator('aside a[href="/app/library"]').first().click();};
page.on('pageerror',e=>report.errors.push(e.name));
page.on('response',async r=>{const u=new URL(r.url());if(u.pathname.startsWith('/v1/'))report.responses.push({path:u.pathname,status:r.status()});});
try{
 await page.goto('http://127.0.0.1:8790/login',{waitUntil:'networkidle'});await page.getByTestId('login-password-input').fill(fs.readFileSync(new URL('state/integration/secrets/operator.txt',root),'utf8').trim());await page.getByTestId('login-submit-btn').click();await page.waitForFunction(()=>document.querySelector('[data-testid="auth-status"]')?.getAttribute('data-actor')==='local-operator');await page.getByRole('link',{name:'View integration status'}).click();await page.waitForURL('**/app');
 await page.getByTestId('profile-dropdown-trigger').click();const profileText=await page.getByTestId('profile-dropdown-panel').innerText();check('Profile uses canonical identity without demo controls',profileText.includes('local-operator')&&!profileText.includes('AI Active')&&!profileText.includes('Demo Controls'));await page.getByTestId('profile-dropdown-trigger').click();
 await library();
 const fixture=documentFixture(kind,id);report.media_kind=kind;report.original_sha256=crypto.createHash('sha256').update(fixture.buffer).digest('hex');
 const uploaded=page.waitForResponse(r=>new URL(r.url()).pathname==='/v1/files'&&r.request().method()==='POST');
 await page.getByTestId('upload-restrictions-ack').check();
 await page.getByTestId('live-upload-input').setInputFiles(fixture);
 const response=await uploaded;check('Browser multipart upload stored',response.status()===200);const receipt=await response.json();report.document_id=receipt.document_id;
 await page.getByTestId('live-upload-receipt').waitFor();check('Upload receipt visible',(await page.getByTestId('live-upload-receipt').innerText()).includes(receipt.document_id));
 await page.waitForFunction(()=>document.querySelector('[data-testid="live-source-index-state"]')?.textContent==='ready',{},{timeout:90000});
 check('Automatic index ready in source inspector',(await page.getByTestId('live-source-index-state').innerText())==='ready');
 await page.getByLabel('Library knowledge question',{exact:true}).fill('reference'+id.replaceAll('-',''));await page.getByRole('button',{name:'Search document knowledge',exact:true}).click();await page.locator('[data-search-source="'+receipt.document_id+'"]').first().waitFor();
 check('Uploaded document discoverable in library content search',(await page.getByTestId('library-search-method').innerText()).includes('MiniLM'));await page.locator('[data-search-source="'+receipt.document_id+'"]').first().click();
 if(isCsv){
 await page.getByLabel('Analysis value column',{exact:true}).fill('2');await page.getByLabel('Analysis group column',{exact:true}).fill('1');await page.getByLabel('Analysis row skip',{exact:true}).fill('1');await page.getByTestId('run-source-analysis').click();await page.getByTestId('analysis-exact-table').waitFor();check('Uploaded CSV exact calculation is 47',(await page.getByTestId('analysis-exact-table').innerText()).includes('47'));
 }
 const downloadEvent=page.waitForEvent('download');await page.getByTestId('live-download-original').click();const download=await downloadEvent;const file=await download.path();check('Browser original download exact bytes',crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex')===report.original_sha256);
 await page.getByTestId('browse-live-knowledge').click();await page.getByTestId('knowledge-coverage').waitFor();check('Automatic source organization visible',await page.getByTestId('knowledge-organization').isVisible());check('Uploaded source has real graph nodes',await page.locator('[data-knowledge-node]').count()>0);await page.locator('[data-knowledge-node]').first().click();await page.getByTestId('live-knowledge-inspector').waitFor();check('Source-bound graph node opens',true);
 await library();await page.getByTestId('live-library-filter').fill('aurora-guide');await page.getByRole('button',{name:'Search library',exact:true}).click();await page.locator('[data-source-id="'+receipt.document_id+'"]').click();await page.getByTestId('ask-live-source').click();
 await page.getByTestId('live-chat-question').fill('How often does the Aurora laboratory replace the ceramic membrane?');const retrievalResponse=page.waitForResponse(r=>new URL(r.url()).pathname==='/v1/chat'&&r.request().method()==='POST');await page.getByTestId('retrieve-chat-evidence').click();const retrieved=await (await retrievalResponse).json();report.retrieval_coverage=retrieved.retrieval_coverage;check('Real MiniLM semantic retrieval active',retrieved.retrieval_coverage?.semantic_state==='ready');
 await page.getByTestId('live-chat-citations').first().waitFor({timeout:120000});const answer=await page.getByTestId('live-chat-answer-text').allInnerTexts();report.answer=answer;check('Browser query returns uploaded 47-day fact',answer.some(t=>t.includes('47')));check('Answer cites uploaded source',await page.locator('[data-testid="live-chat-citations"] a').filter({hasText:'aurora'}).count()>0);
 const generatedResponse=page.waitForResponse(r=>new URL(r.url()).pathname==='/v1/reason'&&r.request().method()==='POST',{timeout:120000});
 await page.getByTestId('live-chat-question').fill('How often does the Aurora laboratory replace the ceramic membrane?');await page.getByTestId('generate-chat-explanation').click();
 const generationResponse=await generatedResponse;const generated=await generationResponse.json();report.generation_http={status:generationResponse.status(),detail:generated.detail};report.generation={answer:generated.answer,mode:generated.mode,run_id:generated.run_id,citation_validation:generated.citation_validation,support_validation:generated.support_validation};
 check('Actual Gemma generation retained',generated.mode==='model_unverified'&&!!generated.run_id&&generated.answer.includes('47')&&generated.citations.some(c=>c.document_id===receipt.document_id));
 await page.getByTestId('live-chat-answer-text').last().waitFor();
 if(isPdf){
 await page.getByTestId('live-chat-citations').last().getByRole('link').first().click();await page.getByTestId('live-pdf-workspace').waitFor();
 await page.waitForFunction(()=>{const c=document.querySelector('[data-testid="live-pdf-canvas"]');return c?.width>0&&c?.height>0;},{},{timeout:60000});
 await page.waitForFunction(()=>document.querySelector('[data-testid="live-pdf-text"]')?.textContent.includes('47'),{},{timeout:60000});
 check('Original PDF renders with searchable source text',true);
 }
 check('Workspace fits browser viewport',await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
 report.status=!report.errors.length&&!report.responses.some(r=>r.status>=500)?'PASS_SCOPED':'FAIL';
}catch(e){report.status='FAIL';report.failure={name:e.name,message:e.message};await page.screenshot({path:'evidence/integration-deployment/upload-workflow-'+id+'.png',fullPage:true,timeout:5000}).catch(()=>{});}
finally{report.identity_unchanged=fs.readFileSync(new URL('state/integration/identity.json',root),'utf8')===identity;if(!report.identity_unchanged)report.status='FAIL';fs.writeFileSync('evidence/integration-deployment/upload-workflow-'+id+'.json',JSON.stringify(report,null,2)+'\n');if(!report.identity_unchanged)report.status='FAIL';await browser.close();console.log(JSON.stringify({status:report.status,run_id:id,media_kind:kind,checks:report.checks,failure:report.failure}));if(report.status!=='PASS_SCOPED')process.exitCode=1;}
