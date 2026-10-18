import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const base = process.env.NOETARIS_AUDIT_URL || 'http://127.0.0.1:8878';
const output = process.env.NOETARIS_AUDIT_OUTPUT || path.resolve('../../evidence/noetaris-integration/frontend-ui-audit.json');
const desktopScreenshot = output.replace(/\.json$/i, '-desktop.png');
const mobileScreenshot = output.replace(/\.json$/i, '-mobile.png');
for (const file of [output, desktopScreenshot, mobileScreenshot]) {
 if (fs.existsSync(file)) throw new Error(`Refusing to overwrite existing audit evidence: ${file}`);
}
fs.mkdirSync(path.dirname(output), { recursive: true });
const source = fs.readFileSync(new URL('../src/App.jsx', import.meta.url), 'utf8');
const patterns = [...source.matchAll(/<Route\s+path="([^"]+)"/g)].map(m => m[1]);
const routes = [...new Set([...patterns.filter(r => r.startsWith('/') && r !== '*' && r !== '/auth/callback'), '/app', ...patterns.filter(r => !r.startsWith('/') && r !== '' && r !== '*').map(r => `/app/${r}`)])];
const urlFor = pattern => pattern.includes(':') ? pattern.replaceAll(':id','audit-placeholder').replaceAll(':provider','audit-provider') : pattern;
const routePatternsToAudit = routes.filter(route => route !== '/app/*');
const browser = await chromium.launch({headless:true});
const results=[], consoleErrors=[], pageErrors=[], failedRequests=[];
try {
 const page=await browser.newPage({viewport:{width:1440,height:900}});
 page.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text());});page.on('pageerror',e=>pageErrors.push(e.message));page.on('requestfailed',r=>failedRequests.push({url:r.url(),error:r.failure()?.errorText}));
 try { await page.goto(new URL('/',base).href,{waitUntil:'domcontentloaded',timeout:5000}); } catch (error) {
   const unavailable={checkedAt:new Date().toISOString(),baseUrl:base,classification:'BLOCKED_UI_UNAVAILABLE',error:error.message.split('\n')[0],routesChecked:0,results:[],note:'No host-accessible UI response was available; no route assertions were performed.'};
       fs.mkdirSync(path.dirname(output),{recursive:true});fs.writeFileSync(output,JSON.stringify(unavailable,null,2)+'\n','utf8');console.log(JSON.stringify(unavailable,null,2));throw new Error('NOETARIS UI unavailable; route assertions were not performed.');
     }
     for(const pattern of routePatternsToAudit){
  const route=urlFor(pattern);
  const ep=pageErrors.length,fr=failedRequests.length;
  const response=await page.goto(new URL(route,base).href,{waitUntil:'networkidle',timeout:20000});
  const root=await page.locator('#root').innerText().catch(()=>''),body=await page.locator('body').innerText().catch(()=>''),side=await page.locator('aside').count().catch(()=>0);
  results.push({path:route,http:response?.status()??null,rendered:root.trim().length>0,authenticatedShell:side>0,explicitDenial:/AUTHENTICATION REQUIRED|Workspace Access Control|LIVE INTEGRATION BLOCKED|not authorized|Access is not verified|server-verified identity/i.test(body),preview:root.slice(0,250),pageErrors:pageErrors.slice(ep),failedRequests:failedRequests.slice(fr)});
 }
 await page.goto(new URL('/',base).href,{waitUntil:'networkidle',timeout:20000});
 await page.screenshot({path:desktopScreenshot});
 const responsive=[];
 for(const width of [390,768,910,1024,1279,1280,1440]){
  await page.setViewportSize({width,height:900});
  const viewport=await page.evaluate(()=>document.documentElement.clientWidth);
  const actionRight=await page.getByTestId('public-getstarted-link').evaluate(el=>el.getBoundingClientRect().right);
  responsive.push({width:viewport,actionRight:Math.round(actionRight),horizontalOverflow:actionRight>viewport+1,desktopNavVisible:await page.locator('[data-testid="public-header"] nav').first().isVisible(),mobileMenuVisible:await page.getByTestId('public-menu-btn').isVisible()});
 }
 const mobile=await browser.newPage({viewport:{width:390,height:844}});await mobile.goto(new URL('/',base).href,{waitUntil:'networkidle',timeout:20000});await mobile.getByTestId('public-menu-btn').click();const menu=await mobile.getByTestId('public-mobile-nav').isVisible();await mobile.screenshot({path:mobileScreenshot});await mobile.close();
 const login=await page.goto(new URL('/login',base).href,{waitUntil:'networkidle',timeout:20000});const loginText=await page.locator('body').innerText();
 const auth=await page.evaluate(async()=>{const c=await fetch('/auth/config',{cache:'no-store'});let j={};try{j=await c.json()}catch{}const s=await fetch('/auth/session',{cache:'no-store'});return{config:c.status,session:s.status,sessionServiceHealthy:s.status<500,google:j.providers?.google,github:j.providers?.github};});
 const loginResponsive=[];
 for(const width of [360,390,768,920,1024,1280]){
  await page.setViewportSize({width,height:844});
  loginResponsive.push(await page.evaluate(()=>({width:document.documentElement.clientWidth,scrollWidth:document.documentElement.scrollWidth,bodyScrollWidth:document.body.scrollWidth})));
 }
 await page.setViewportSize({width:1440,height:900});
 const providerButtonsDisabled={google:await page.getByTestId('login-google-btn').isDisabled(),github:await page.getByTestId('login-github-btn').isDisabled()};
 const localCredentialSubmitDisabled=await page.getByTestId('login-submit-btn').isDisabled();
 const dynamicLiveRoutes=new Set(['/app/chat/:id','/app/documents/:id','/app/workflows/:id/edit','/app/executions/:id']);
   const routeEvidence=results.map((item,index)=>({...item,pattern:routePatternsToAudit[index],expectedGate:dynamicLiveRoutes.has(routePatternsToAudit[index])?'existing auth/admission policy':routePatternsToAudit[index].startsWith('/app/')?'live page/auth gate':'public page'}));
 const appRoutes=results.filter(item=>item.path==='/app'||item.path.startsWith('/app/'));
 const protectedRoutesGated=appRoutes.length>0&&appRoutes.every(item=>item.explicitDenial);
 const authReady=auth.config===200&&auth.sessionServiceHealthy&&typeof auth.google==='boolean'&&typeof auth.github==='boolean';
 const providerControlsSafe=(auth.google!==false||providerButtonsDisabled.google)&&(auth.github!==false||providerButtonsDisabled.github);
 const loginOverflow=loginResponsive.filter(item=>item.scrollWidth>item.width+1||item.bodyScrollWidth>item.width+1);
 const responsiveOverflow=responsive.filter(item=>item.horizontalOverflow||item.mobileMenuVisible!==(item.width<1280)||item.desktopNavVisible!==(item.width>=1280));
 const evidence={checkedAt:new Date().toISOString(),baseUrl:base,authentication:'anonymous browser; no credential is loaded or inserted by this auditor',routePatterns:routePatternsToAudit,routesChecked:results.length,results:routeEvidence,protectedRoutesGated,auth,authReady,providerButtonsDisabled,localCredentialSubmitDisabled,providerControlsSafe,responsive,responsiveOverflow,loginResponsive,loginOverflow,loginVisible:loginText.includes('Sign in to Noetaris'),providerSettingsVisible:loginText.includes('Google')&&loginText.includes('GitHub'),publicMobileMenuWorks:menu,screenshots:{desktop:desktopScreenshot,mobile:mobileScreenshot},consoleErrors,pageErrors,failedRequests,note:'Anonymous route render, access-gate, and responsive-layout checks only. Authentication must be completed manually by an authorized user. This does not certify sign-in or feature workflows.'};
 fs.writeFileSync(output,JSON.stringify(evidence,null,2)+'\n','utf8');
 console.log(JSON.stringify({output,routes:results.length,failures:results.filter(r=>r.http!==200||!r.rendered||r.pageErrors.length||r.failedRequests.length||(r.path==='/app'||r.path.startsWith('/app/'))&&!r.explicitDenial),protectedRoutesGated,auth,authReady,providerButtonsDisabled,localCredentialSubmitDisabled,providerControlsSafe,responsiveOverflow,loginOverflow,menu,errors:pageErrors,failedRequests},null,2));
 if(results.some(r=>r.http!==200||!r.rendered||r.pageErrors.length||r.failedRequests.length||(r.path==='/app'||r.path.startsWith('/app/'))&&!r.explicitDenial)||pageErrors.length||failedRequests.length||!menu||!protectedRoutesGated||responsiveOverflow.length||loginOverflow.length||!authReady||!providerControlsSafe||!loginText.includes('Sign in to Noetaris')||(auth.config===200&&(typeof auth.google!=='boolean'||typeof auth.github!=='boolean')))process.exitCode=1;
} finally { await browser.close(); }
