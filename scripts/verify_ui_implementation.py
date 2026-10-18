"""Chromium with real public static routes and synthetic content API fixtures."""
import asyncio, hashlib, io, json, time, os, uuid, socket, subprocess, sys
from contextlib import contextmanager
import urllib.request
from pathlib import Path
from urllib.parse import parse_qs
from playwright.async_api import async_playwright
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject,NameObject,DecodedStreamObject
from check_release_readiness import source_snapshot
ROOT=Path(__file__).resolve().parents[1]
DPR=float(os.getenv('NSAI_BROWSER_DPR','1'))
if DPR not in {1,2,3}:raise ValueError('Browser DPR must be 1, 2 or 3')
@contextmanager
def static_server(cleanup):
 with socket.socket() as listener:
  listener.bind(('127.0.0.1',0));port=listener.getsockname()[1]
 environment={key:value for key,value in os.environ.items() if not key.startswith('NSAI_')}
 environment.update(PYTHONPATH=str(ROOT/'src'),PYTHONDONTWRITEBYTECODE='1')
 process=subprocess.Popen([sys.executable,'-m','uvicorn','nsai.api:app','--host','127.0.0.1','--port',str(port),
    '--lifespan','off','--no-access-log','--log-level','error'],cwd=ROOT,env=environment,
    stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
    creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
 cleanup.update(created=True,stopped=False)
 origin='http://127.0.0.1:'+str(port)
 try:
  deadline=time.monotonic()+20
  while time.monotonic()<deadline:
   if process.poll() is not None:raise RuntimeError('Owned static API process failed to start')
   try:
    with urllib.request.urlopen(origin+'/healthz',timeout=1) as response:
     if response.status==200:break
   except OSError:pass
   time.sleep(.1)
  else:raise RuntimeError('Owned static API startup deadline exceeded')
  yield origin
 finally:
  try:
   if process.poll() is None:process.terminate()
   try:process.wait(timeout=5)
   except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
  finally:cleanup['stopped']=process.poll() is not None


async def run(static_origin):
 writer=PdfWriter();native=writer.add_blank_page(width=200,height=300);writer.add_js("app.alert('must not execute')")
 font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
 native[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):writer._add_object(font)})})
 content=DecodedStreamObject();content.set_data(b'BT /F1 10 Tf 20 240 Td (Unique motor limit is 85 C.) Tj 0 -25 Td (Repeated quote.) Tj 0 -25 Td (Repeated quote.) Tj ET')
 native[NameObject('/Contents')]=writer._add_object(content)
 buf=io.BytesIO();writer.write(buf);pdf=buf.getvalue();original_pdf=pdf
 oversized=PdfWriter();oversized.add_blank_page(width=20000,height=1);oversized_buffer=io.BytesIO();oversized.write(oversized_buffer);oversized_pdf=oversized_buffer.getvalue()

 ocr_folder=ROOT/'evidence/ocr-geometry-requalification/6115e87c2baf4737b6f639bac749ae55'
 ocr_pdf=(ocr_folder/'original-raster.pdf').read_bytes();ocr_raw=(ocr_folder/'worker-output.json').read_bytes()
 assert hashlib.sha256(ocr_pdf).hexdigest()=='6240ae17c53837340cde1d6cd94b42635a5072ca3d64d9d109b6c9fca995e980'
 assert hashlib.sha256(ocr_raw).hexdigest()=='2cf03c93ea0939b8153f14a467620b4d7d296be3c4391192cf1cbd150847245a'
 ocr_parsed=json.loads(ocr_raw);assert ocr_parsed['original_sha256']==hashlib.sha256(ocr_pdf).hexdigest()

 native.rotate(90);buf=io.BytesIO();writer.write(buf);rotated_pdf=buf.getvalue()
 docid='a'*32
 checks=[];errors=[];warnings=[];asks=[];network=[];delay=False;fail=False;role='admin';policy_state='pending';record_state='candidate';many_records=False;claims_failed=False;claims_incomplete=False;ocr_mode=False;auth_denied=False;font_unavailable=False;font_corrupt=False
 async with async_playwright() as p:
  executable=os.getenv('NSAI_BROWSER_EXECUTABLE');candidates=list((Path(os.getenv('LOCALAPPDATA',''))/'ms-playwright').glob('chromium-*/chrome-win64/chrome.exe'));executable=executable or (str(sorted(candidates)[-1]) if candidates else None)
  browser=await p.chromium.launch(headless=True,**({'executable_path':executable} if executable else {}))
  page=await browser.new_page(device_scale_factor=DPR);page.set_default_timeout(10000);page.on('pageerror',lambda err:errors.append(str(err)))
  page.on('console',lambda message:warnings.append(message.text) if message.type=='warning' else None)
  async def intercept(route):
   nonlocal delay,fail,policy_state,record_state
   path=route.request.url.split('http://127.0.0.1:18879')[-1]
   network.append(path)
   if path.startswith('/v1/') and auth_denied:await route.fulfill(status=401,json={'detail':'Synthetic credential revoked'});return
   if path.startswith('/v1/claims') and claims_failed:await route.fulfill(status=503,json={'detail':'Synthetic claim projection unavailable'});return
   if path.startswith('/assets/pdfjs/standard_fonts/') and font_unavailable:await route.fulfill(status=404,body='Missing fixture font');return
   if path.startswith('/assets/pdfjs/standard_fonts/') and font_corrupt:await route.fulfill(status=200,body=b'corrupted-font-fixture',content_type='application/octet-stream');return
   if path=='/' or path.startswith('/assets/'):
    response=await route.fetch(url=static_origin+path)
    await route.fulfill(response=response);return
   if path=='/auth/config':data={'providers':{'google':False,'github':False},'csrf':None}
   elif path=='/v1/capabilities':data={'capabilities':[{'id':'synthetic-registry','state':'staged','evidence':'string-shaped backward-compatible receipt','permissions':'read','routes':'/synthetic'}],'identity':{'role':role,'permissions':{'viewer':['read'],'operator':['read','chat','ingest','propose'],'reviewer':['read','review'],'admin':['read','review','admin']}[role]}}
   elif path.startswith('/v1/documents?'):
    query=parse_qs(path.partition('?')[2]);offset=int(query.get('cursor',['0'])[0]);term=query.get('q',[''])[0].lower()
    items=[{'id':docid,'title':'<img src=x onerror=alert(1)>' if index==0 else f'Fixture source {index+1}','version':'1','sha256':'b'*64} for index in range(100)]
    items=[item for item in items if term in item['title'].lower()];total=len(items)
    data={'items':items[offset:offset+25],'total':total,'has_more':offset+25<total,'next_cursor':str(offset+25) if offset+25<total else None}
   elif path.startswith('/v1/claims?'):
    query=parse_qs(path.partition('?')[2]);offset=int(query.get('cursor',['0'])[0])
    data={'items':[{'id':str(i),'subject':'S','predicate':'P','value':'1','status':'candidate','revision':1,'locator':'page:1','document_id':docid} for i in range(offset,min(offset+25,2000))],
          'total':2000,'has_more':offset+25<2000,'next_cursor':str(offset+25) if offset+25<2000 else None,'conflicts':[],
          'summary':{'verified_claims':42,'active_conflict_groups':None if claims_incomplete else 0,'conflict_analysis_complete':not claims_incomplete,'warning':'Conflict analysis exceeds the qualified bound.' if claims_incomplete else None}}
   elif path=='/v1/admin/security':data={'policy':{'revision':1,'inference_enabled':True,'daily_call_limit':100,'max_output_tokens':256,'central_config':{'enabled':False,'provider':'none','issuer':None}}}
   elif path=='/v1/admin/policy':data={'state':'pending-independent-review','action_id':'e'*64,'policy_unchanged':True,'authority_granted':False}
   elif path=='/v1/admin/actions':data={'items':[{'id':'e'*64,'requested_by':'local-admin','policy_revision':1,'payload':{'daily_call_limit':101,'central_config':{'enabled':False}},'state':policy_state,'expires_at':'2099-01-01T00:00:00Z'}]}
   elif path.startswith('/v1/admin/actions/') and path.endswith('/review'):
    policy_state='applied' if route.request.post_data_json['approve'] else 'rejected';data={'state':policy_state,'audit_receipt':'f'*64}
   elif path.startswith('/v1/governed/records?'):
    if role=='viewer':items=[]
    elif many_records:
     offset=int(path.split('offset=')[1]);items=[{'id':format(index,'064x'),'kind':'issues','author':'local-operator','document_id':docid,'source_sha256':hashlib.sha256(pdf).hexdigest(),'state':'candidate'} for index in range(offset,min(offset+25,26))]
    else:items=[{'id':'d'*64,'kind':'issues','author':'local-operator','document_id':docid,'source_sha256':hashlib.sha256(pdf).hexdigest(),'state':record_state}]
    data={'items':items}
   elif path.startswith('/v1/governed/records/') and path.endswith('/review'):
    record_state=route.request.post_data_json['decision'];data={'state':record_state,'authority_granted':False,'audit_receipt':'f'*64}
   elif path.startswith('/v1/governed/records/'):
    data={'id':'d'*64,'kind':'issues','author':'local-operator','document_id':docid,'source_sha256':hashlib.sha256(pdf).hexdigest(),'state':record_state,'payload':{'flow':['evidence','engineering issue classification','candidate review'],'execution_enabled':False}}
   elif path=='/v1/issues/analyze':data={'id':'d'*64,'state':'candidate','authority_granted':False,'created':True,'audit_receipt':'f'*64}
   elif path=='/v1/admin/retention':data={'state':'inspection-only','delete_enabled':False,'automatic_cleanup':False,'counts':{'documents':1}}
   elif path=='/v1/submission/evidence':data={'receipts':[{'name':'synthetic missing binding','status':'PASS','exit_code':0,'output_sha256':'b'*64}]}
   elif path.startswith('/v1/memory/'):
    await asyncio.sleep(1);data={'marker':'OLD_SCOPE_PRIVATE_MEMORY'}
   elif path=='/v1/model/status':data={'reachable':True,'model_loaded':True,'provider':'synthetic','model':'fixture'}
   elif path.startswith('/v1/sources/') and path.endswith('/original'):
    await route.fulfill(body=pdf,content_type='application/pdf');return
   elif path.startswith('/v1/sources/'):data={'id':docid,'title':'synthetic','revision':'1','original_sha256':hashlib.sha256(pdf).hexdigest(),'media_type':'application/pdf','manifest':{'metadata':{'pages':[{'page':1,'status':'blank'}]}}}
   elif path in ['/v1/chat','/v1/reason']:
    asks.append(route.request.post_data_json)
    if fail:
     await route.fulfill(status=503,json={'detail':'Synthetic model unavailable'});return
    if delay:await asyncio.sleep(1)
    data={'session_id':'c'*32,'answer':'Synthetic fixture answer','mode':'fixture','citations':[{'chunk_id':'f'*32,'document_id':docid,'locator':'page:1','revision':'1','original_sha256':hashlib.sha256(pdf).hexdigest(),'extraction_complete':False,'page_coverage':[{'page':1,'status':'ocr_required'}]}]}
   else:await route.fulfill(status=404,json={'detail':'unexpected fixture path'});return
   if path.startswith('/v1/sources/') and not path.endswith('/original') and ocr_mode:data['manifest']={'documents':[{'metadata':{'pages':ocr_parsed['pages'],'ocr_words':ocr_parsed['ocr_words']}}]}
   await route.fulfill(json=data)
  await page.context.route('**/*',intercept)
  await page.goto('http://127.0.0.1:18879')
  await page.wait_for_function("() => document.getElementById('oauth-status').textContent.includes('not configured')")
  for provider in ['google','github']:
   for mode in ['login','signup','link']:
    assert await page.locator('#oauth-'+provider+'-'+mode).is_disabled()
  checks.append({'name':'disabled provider configuration is explicit and local credentials remain available','status':'PASS'})
  for role in ['operator','reviewer','admin']:
   await page.locator('#token').fill('synthetic-not-a-credential');await page.locator('#connect').click()
   await page.wait_for_function("role => document.getElementById('identity').textContent.startsWith(role)",arg=role)
   assert await page.locator('#save-policy').is_disabled()==(role!='admin')
   assert await page.locator('#load-learning').is_disabled()==(role=='operator')
   assert await page.locator('#upload').is_disabled()==(role!='operator')
  checks.append({'name':'operator/reviewer/admin controls reflect synthetic server permissions','status':'PASS'})
  await page.locator('[data-view=governance]').click();await page.locator('#load-policy').click()
  await page.wait_for_function("() => document.getElementById('daily-limit').value==='100'")
  await page.locator('#daily-limit').fill('101');await page.locator('#save-policy').click()
  await page.wait_for_function("() => document.getElementById('notice').textContent.startsWith('Policy unchanged')")
  assert await page.locator('#daily-limit').input_value()=='100'
  await page.locator('#load-retention').click();await page.wait_for_function("() => document.getElementById('retention-data').textContent.includes('inspection-only')")
  await page.locator('[data-view=governed]').click();await page.locator('#load-actions').click()
  await page.wait_for_function("() => document.getElementById('policy-actions').textContent.includes('local-admin')")
  assert await page.locator('#policy-actions button').filter(has_text='Approve independent action').is_disabled()
  role='reviewer';await page.locator('#token').fill('synthetic');await page.locator('#connect').click()
  await page.wait_for_function("() => document.getElementById('identity').textContent.startsWith('reviewer')")
  await page.locator('[data-view=governed]').click();await page.locator('#load-actions').click()
  await page.locator('#policy-actions button').filter(has_text='Approve independent action').click()
  await page.wait_for_function("() => document.getElementById('notice').textContent.includes('Policy action applied')")
  await page.locator('#load-governed').click();assert await page.locator('#governed-records button').filter(has_text='Review candidate').is_disabled();await page.locator('#governed-records button').filter(has_text='Inspect source-bound payload').click();await page.locator('#governed-rationale').fill('Independent synthetic source record review')
  await page.locator('#governed-records button').filter(has_text='Review candidate').click()
  await page.wait_for_function("() => document.getElementById('notice').textContent.includes('no factual or execution authority')")
  assert 'reviewed' in await page.locator('#governed-records').inner_text()
  checks.append({'name':'pending policy unchanged, self-approval disabled, independent reviewer applies action and reviews record without granting truth/execution; retention inspection only','status':'PASS'})
  role='operator';await page.locator('#token').fill('synthetic');await page.locator('#connect').click()
  await page.wait_for_function("() => document.getElementById('identity').textContent.startsWith('operator')")
  many_records=True
  await page.locator('[data-view=governed]').click();await page.locator('#load-governed').click()
  await page.wait_for_function("() => document.querySelectorAll('#governed-records .card').length===25")
  await page.locator('#governed-next').click();await page.wait_for_function("() => document.getElementById('governed-status').textContent.includes('offset 25')")
  assert await page.locator('#governed-records .card').count()==1
  assert await page.locator('#governed-next').is_disabled()
  checks.append({'name':'governed records fetch authorized server pages 0 and 25; last short page ends navigation','status':'PASS'})
  role='viewer';await page.locator('#token').fill('synthetic');await page.locator('#connect').click()
  await page.wait_for_function("() => document.getElementById('identity').textContent.startsWith('viewer')")
  await page.locator('[data-view=governed]').click();await page.locator('#load-governed').click()
  await page.wait_for_function("() => document.getElementById('governed-status').textContent.startsWith('Showing 0')")
  assert await page.locator('#governed-records .card').count()==0
  assert await page.locator('#load-actions').is_disabled()
  checks.append({'name':'viewer synthetic author-filtered empty records does not show another actor proposal or policy action controls','status':'PASS'})
  role='operator';await page.locator('#token').fill('synthetic');await page.locator('#connect').click()
  await page.wait_for_function("() => document.getElementById('identity').textContent.startsWith('operator')")
  await page.wait_for_function("() => document.getElementById('document-count').textContent==='100'")
  assert await page.locator('#documents .card').count()==25
  await page.locator('[data-view=sources]').click();await page.locator('#library-next').click()
  await page.wait_for_function("() => document.getElementById('library-status').textContent.includes('page 2')")
  assert 'Fixture source 26' in await page.locator('#documents .card').first.inner_text()
  await page.locator('#library-prev').click()
  await page.wait_for_function("() => document.getElementById('library-status').textContent.includes('page 1')")
  await page.locator('#library-query').fill('Fixture source 2');await page.locator('#library-search').click()
  await page.wait_for_function("() => document.getElementById('document-count').textContent==='11'")
  assert await page.locator('#documents .card').count()==11 and await page.locator('#library-next').is_disabled()
  await page.locator('#library-query').fill('');await page.locator('#library-search').click()
  await page.wait_for_function("() => document.getElementById('document-count').textContent==='100'")
  checks.append({'name':'library fetches bounded server pages with opaque cursor and title filter; previous navigation and filter reset are explicit','status':'PASS'})
  claims_failed=True
  await page.locator('#view-sources .refresh').click()
  await page.wait_for_function("() => document.getElementById('claims').textContent.includes('projection unavailable')")
  assert await page.locator('#documents .card').count()==25
  assert await page.locator('#conflict-count').inner_text()=='—'
  claims_failed=False;await page.locator('#view-sources .refresh').click()
  await page.wait_for_function("() => document.querySelectorAll('#claims .card').length===25")
  checks.append({'name':'claim projection failure preserves library browsing and reports unknown conflict counts; refresh recovers','status':'PASS'})
  assert await page.locator('#claims .card').count()==25
  assert await page.locator('#documents img').count()==0
  await page.locator('[data-view=review]').click();await page.locator('#claims-next').click()
  await page.wait_for_function("() => document.querySelector('#claims .card small').textContent.startsWith('25 ')")
  assert await page.locator('#claims .card').count()==25
  assert await page.locator('#verified-count').inner_text()=='42'
  await page.locator('#claims-prev').click()
  await page.wait_for_function("() => document.querySelector('#claims .card small').textContent.startsWith('0 ')")
  checks.append({'name':'library and review fetch 25-row server pages; review totals are independent of displayed candidate rows; inert title and previous navigation','status':'PASS'})
  claims_incomplete=True;await page.locator('#view-review .refresh').click()
  await page.wait_for_function("() => document.getElementById('conflicts').textContent.includes('qualified bound')")
  assert await page.locator('#conflict-count').inner_text()=='\u2014'
  assert await page.locator('#claims .card').count()==25
  claims_incomplete=False;await page.locator('#view-review .refresh').click()
  await page.wait_for_function("() => document.getElementById('conflict-count').textContent==='0'")
  checks.append({'name':'incomplete global conflict analysis reports unknown count while retaining review pages; fresh complete analysis recovers','status':'PASS'})
  await page.locator('[data-view=verification]').click();await page.locator('#load-verification').click();await page.wait_for_function("() => document.getElementById('evidence-status').textContent.startsWith('UNVERIFIED')")
  assert 'missing source binding' in await page.locator('#evidence-status').inner_text()
  checks.append({'name':'evidence panel does not promote historical incomplete PASS receipt to qualification','status':'PASS'})
  await page.evaluate("() => inspect('a'.repeat(32))")
  await page.locator('#assemble-source').click();await page.wait_for_function("() => document.getElementById('assembly-receipt').textContent.includes('candidate')");assert 'No reviewed authority or execution granted' in await page.locator('#notice').inner_text()
  await page.locator('#open-pdf').click();await page.wait_for_function("() => document.getElementById('pdf-status').textContent.includes('page 1/1')")
  assert await page.locator('#pdf-canvas').evaluate('(c)=>c.width')==200*DPR
  assert any('/assets/pdfjs/standard_fonts/LiberationSans-Regular.ttf' in path for path in network)
  assert not any('standardFontDataUrl' in message for message in warnings),warnings
  assert await page.locator('#pdf-canvas').evaluate('(c)=>{const p=c.getContext("2d").getImageData(0,0,c.width,c.height).data;let n=0;for(let i=0;i<p.length;i+=4)if(Math.min(p[i],p[i+1],p[i+2])<128)n++;return n;}')>100
  checks.append({'name':'real static server supplies pinned local standard font data; native canvas has visible ink without missing-font-data warnings','status':'PASS'})
  async def citation(quote,digest=None):
   anchor=dict(schema='nsai.citation-anchor/1',document_id=docid,original_sha256=digest or hashlib.sha256(pdf).hexdigest(),revision='1',page=1,
       selector=dict(type='TextQuoteSelector',exact=quote),quote_sha256=hashlib.sha256(quote.encode()).hexdigest())
   await page.evaluate('(anchor)=>inspect("a".repeat(32),"page:1:line:1",anchor)',anchor)
  await citation('Unique motor limit is 85 C.')
  assert 'Unique native text match highlighted' in await page.locator('#pdf-status').inner_text()
  boxes=await page.locator('.pdf-quote-mark').evaluate_all('(marks)=>marks.map(m=>({x:parseFloat(m.style.left),y:parseFloat(m.style.top),width:parseFloat(m.style.width),height:parseFloat(m.style.height)}))')
  assert boxes and abs(boxes[0]['x']-20)<2 and 45<boxes[0]['y']<65 and boxes[0]['width']>100,boxes
  await page.locator('#pdf-zoom').select_option('1.5')
  await page.wait_for_function("() => document.getElementById('pdf-canvas').width===300*window.devicePixelRatio && document.querySelector('.pdf-quote-mark')")
  zoomed=await page.locator('.pdf-quote-mark').first.evaluate('(m)=>parseFloat(m.style.width)')
  assert abs(zoomed/boxes[0]['width']-1.5)<.05,(zoomed,boxes)
  await page.set_viewport_size({'width':390,'height':844})
  resized=await page.locator('.pdf-quote-mark').first.evaluate('(m)=>{const c=document.getElementById("pdf-canvas").getBoundingClientRect(),b=m.getBoundingClientRect();return {x:b.x-c.x,y:b.y-c.y,width:b.width};}')
  assert abs(resized['x']-30)<2 and abs(resized['y']-boxes[0]['y']*1.5)<2 and abs(resized['width']-zoomed)<1,resized
  await page.set_viewport_size({'width':1280,'height':720})
  checks.append({'name':f'native backing pixels follow DPR {DPR:g}; CSS citation geometry remains aligned at 150% zoom and mobile resize','status':'PASS'})
  await citation('Repeated quote.')
  assert 'more than once' in await page.locator('#pdf-status').inner_text() and await page.locator('.pdf-quote-mark').count()==0
  await citation('Absent OCR quote')
  assert 'could not be uniquely aligned' in await page.locator('#pdf-status').inner_text() and await page.locator('.pdf-quote-mark').count()==0
  await citation('Unique motor limit is 85 C.',digest='0'*64)
  assert 'No passage selected' in await page.locator('#pdf-status').inner_text() and await page.locator('.pdf-quote-mark').count()==0
  pdf=rotated_pdf
  await citation('Unique motor limit is 85 C.')
  assert await page.locator('#pdf-canvas').evaluate('(c)=>c.width')==300*DPR
  rotated=await page.locator('.pdf-quote-mark').first.evaluate('(m)=>({x:parseFloat(m.style.left),y:parseFloat(m.style.top),width:parseFloat(m.style.width),height:parseFloat(m.style.height)})')
  assert 230<rotated['x']<260 and abs(rotated['y']-20)<2 and rotated['height']>100,rotated
  pdf=original_pdf;await citation('Unique motor limit is 85 C.')
  pdf=oversized_pdf
  try:await citation('Unique motor limit is 85 C.')
  except Exception as error:assert 'pixel budget' in str(error),str(error)
  else:raise AssertionError('Excessive page dimension was admitted')
  assert await page.locator('.pdf-quote-mark').count()==0
  assert await page.locator('#pdf-canvas').evaluate('(c)=>c.width*c.height')==0
  assert await page.locator('#pdf-text').inner_text()==''
  pdf=original_pdf;await citation('Unique motor limit is 85 C.')
  checks.append({'name':'oversized page refusal removes previous ink, source text and highlights before allocation; next valid page recovers','status':'PASS'})
  font_unavailable=True;await citation('Unique motor limit is 85 C.')
  assert 'resource is unavailable' in await page.locator('#pdf-status').inner_text()
  assert await page.locator('.pdf-quote-mark').count()==0
  font_unavailable=False;await citation('Unique motor limit is 85 C.')
  assert 'Unique native text match highlighted' in await page.locator('#pdf-status').inner_text()
  font_corrupt=True;await citation('Unique motor limit is 85 C.')
  assert 'resource is unavailable' in await page.locator('#pdf-status').inner_text()
  assert await page.locator('.pdf-quote-mark').count()==0
  font_corrupt=False;await citation('Unique motor limit is 85 C.')
  assert 'Unique native text match highlighted' in await page.locator('#pdf-status').inner_text()
  checks.append({'name':'font bytes must match pinned SHA256 before parsing; corrupted HTTP200 font data withholds highlighting','status':'PASS'})
  checks.append({'name':'missing local font data explicitly withholds passage highlighting; a fresh successful load restores matching','status':'PASS'})
  checks.append({'name':'native PDF text quote opens exact revision/page, unique passage highlights with measured zoom/rotation geometry; duplicate/missing/hash mismatch never guessed','status':'PASS'})
  ocr_mode=True;pdf=ocr_pdf
  await citation('Pump Valve Inlet Rotor')
  assert 'Unique OCR word regions highlighted' in await page.locator('#pdf-status').inner_text(),await page.locator('#pdf-status').inner_text()
  assert await page.locator('.pdf-quote-mark').count()==4
  ocr_box=await page.locator('.pdf-quote-mark').first.evaluate('(m)=>({x:parseFloat(m.style.left),y:parseFloat(m.style.top),width:parseFloat(m.style.width),height:parseFloat(m.style.height)})')
  assert abs(ocr_box['x']-19.44)<.02 and abs(ocr_box['y']-26.16)<.02,ocr_box
  assert await page.locator('#pdf-canvas').evaluate('(c,b)=>{const pixels=c.getContext("2d").getImageData(Math.floor(b.x*c.width/c.clientWidth),Math.floor(b.y*c.height/c.clientHeight),Math.ceil(b.width*c.width/c.clientWidth),Math.ceil(b.height*c.height/c.clientHeight)).data;let ink=0;for(let i=0;i<pixels.length;i+=4)if(pixels[i]<160)ink++;return ink;}',ocr_box)>15

  await page.locator('#pdf-zoom').select_option('1.5')
  await page.wait_for_function("() => document.getElementById('pdf-canvas').width===432*window.devicePixelRatio && document.querySelector('.pdf-quote-mark')")
  ocr_zoom=await page.locator('.pdf-quote-mark').first.evaluate('(m)=>parseFloat(m.style.width)')
  assert abs(ocr_zoom/ocr_box['width']-1.5)<.02
  await citation('Pump')
  assert await page.locator('.pdf-quote-mark').count()==1  # Same word on other pages must not create ambiguity.
  await citation('Missing raster phrase')
  assert await page.locator('.pdf-quote-mark').count()==0
  original_words=json.loads(json.dumps(ocr_parsed['ocr_words']))
  ocr_parsed['ocr_words'][0]['pdf_box'][0]+=1
  await citation('Pump Valve Inlet Rotor')
  assert 'coordinate custody' in await page.locator('#pdf-status').inner_text() and await page.locator('.pdf-quote-mark').count()==0
  ocr_parsed['ocr_words']=original_words+[word for word in original_words if word['page']==1]
  await citation('Pump')
  assert 'more than once' in await page.locator('#pdf-status').inner_text() and await page.locator('.pdf-quote-mark').count()==0
  ocr_parsed['ocr_words']=original_words

  ocr_mode=False;pdf=original_pdf;await citation('Unique motor limit is 85 C.')
  checks.append({'name':'actual pinned OCR words map a unique page-bound quote to raster PDF regions with measured zoom geometry; other pages and missing quotes never guessed','status':'PASS'})
  checks.append({'name':'OCR coordinate tampering and duplicate page-local matches suppress all highlights; measured rectangle covers actual raster ink','status':'PASS'})
  await page.locator('#question').fill('Scoped fixture question');await page.locator('#send').click();await page.wait_for_function("() => document.getElementById('chat-status').textContent.startsWith('Sources are')")
  assert 'Incomplete source extraction' in await page.locator('#source-safety').inner_text()
  checks.append({'name':'incomplete source coverage displayed separately from answer quality','status':'PASS'})
  assert len(asks[-1]['request_id'])==32 and '-' not in asks[-1]['request_id']
  assert not asks[-1].get('document_ids') and not asks[-1].get('pages'), 'Viewing a PDF must not silently narrow chat scope'
  await page.locator('#chat-scope').select_option('page')
  await page.locator('#question').fill('Explicit page question');await page.locator('#send').click();await page.wait_for_function("() => document.getElementById('chat-status').textContent.startsWith('Sources are')")
  assert asks[-1]['document_ids']==[docid] and asks[-1]['pages']==[1] and asks[-1]['revision']=='1'
  assert asks[-1]['session_id'] is None
  checks.append({'name':'opening PDF leaves library scope; explicitly selecting page starts new session and sends revision/page; no PDF JS action','status':'PASS'})
  await page.locator('#chat-scope').select_option('document')
  await page.evaluate("() => inspect('b'.repeat(32))")
  await page.locator('#question').fill('Fixed page scope after viewing another source');await page.locator('#send').click();await page.wait_for_function("() => document.getElementById('chat-status').textContent.startsWith('Sources are')")
  assert asks[-1]['document_ids']==[docid] and not asks[-1].get('pages')
  await page.locator('#apply-chat-scope').click()
  await page.locator('#question').fill('Rebound source question');await page.locator('#send').click();await page.wait_for_function("() => document.getElementById('chat-status').textContent.startsWith('Sources are')")
  assert asks[-1]['document_ids']==['b'*32] and asks[-1]['session_id'] is None
  await page.locator('[data-view=memory]').click();await page.locator('#refresh-memory').click()
  await page.locator('[data-view=chat]').click()
  await page.locator('#chat-scope').select_option('library')
  await asyncio.sleep(1.2)
  assert 'OLD_SCOPE_PRIVATE_MEMORY' not in await page.locator('#memory-data').inner_text()
  checks.append({'name':'Apply rebinds current source without toggling selector; late memory refresh cannot cross scope','status':'PASS'})
  assert await page.locator('#chat-scope').input_value()=='library'
  delay=True
  await page.locator('#question').fill('Old scope request');await page.locator('#send').click()
  await page.wait_for_function("() => document.getElementById('model').disabled")
  await page.locator('#chat-scope').select_option('document')
  await asyncio.sleep(1.2)
  assert 'Question scope changed' in await page.locator('#chat-status').inner_text()
  assert await page.evaluate('sessionId') is None
  assert not await page.locator('#send').is_disabled()
  delay=False
  checks.append({'name':'source inspection preserves fixed question scope; scope change discards late answers and starts fresh session','status':'PASS'})
  fail=True
  await page.locator('#question').fill('Retain this failed question');await page.locator('#send').click()
  await page.wait_for_function("() => document.getElementById('chat-status').textContent.startsWith('Request failed')")
  assert await page.locator('#question').input_value()=='Retain this failed question'
  assert not await page.locator('#send').is_disabled()
  checks.append({'name':'failed ask exits pending, retains question and exposes retry receipt caution','status':'PASS'})
  fail=False
  await page.locator('#question').fill('PRIVATE DRAFT BEFORE REVOCATION')
  auth_denied=True
  await page.evaluate("() => request('/v1/documents?limit=25').catch(()=>{})")
  assert await page.locator('#identity').inner_text()=='Disconnected'
  assert await page.locator('#question').input_value()=='' and await page.locator('#feed').inner_text()==''
  assert await page.locator('#pdf-canvas').evaluate('(c)=>c.width')==0
  assert await page.evaluate('libraryCursor===null && libraryBack.length===0 && token===""')
  auth_denied=False;await page.locator('#token').fill('synthetic');await page.locator('#connect').click()
  await page.wait_for_function("() => document.getElementById('identity').textContent.startsWith('operator')")
  checks.append({'name':'server credential rejection clears drafts, answers, PDF, pagination and in-memory token before reconnect','status':'PASS'})
  delay=True
  await page.locator('#question').fill('Delayed synthetic question');await page.locator('#send').click()
  assert await page.locator('#model').is_disabled()
  for name in ['document','docname','reflection','rationale','learning-claim']:
   await page.locator('#'+name).evaluate("element=>element.value='PRIVATE DRAFT'")
  await page.locator('#file').set_input_files({'name':'synthetic.txt','mimeType':'text/plain','buffer':b'PRIVATE'})
  await page.locator('#disconnect').click();await asyncio.sleep(1.2)
  for name in ['question','document','docname','reflection','rationale','learning-claim','file','central-issuer']:
   assert await page.locator('#'+name).input_value()=='',(name,errors)
  assert await page.locator('#feed').inner_text()==''
  assert await page.locator('#pdf-canvas').evaluate('(c)=>c.width')==0
  assert await page.locator('#identity').inner_text()=='Disconnected'
  assert len({request['request_id'] for request in asks})==len(asks)
  assert await page.locator('#governed-detail').inner_text()==''
  checks.append({'name':'deliberate asks receive unique 32-hex durable request keys, with no automatic resend; governed payload cleared','status':'PASS'})
  checks.append({'name':'disconnect clears all drafts/file/PDF buffers; late old-epoch ask does not repopulate','status':'PASS'})
  await page.set_viewport_size({'width':390,'height':844});await page.evaluate('() => new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
  assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth+1'), await page.evaluate("[innerWidth,document.documentElement.scrollWidth,document.body.scrollWidth,Array.from(document.querySelectorAll('*')).filter(e=>e.scrollWidth>e.clientWidth+5).map(e=>[e.tagName,e.id,e.className,e.scrollWidth,e.clientWidth]).slice(0,20)]")
  checks.append({'name':'390px mobile viewport has no page-level horizontal overflow','status':'PASS'})
  assert not errors,errors
  await browser.close()
 return {'device_pixel_ratio':DPR,'method':'Actual Chromium and owned real application HTTP static server; intercepted synthetic content API/PDF; no live DB/model or credentials','checks':checks,'page_errors':errors,'elapsed_seconds':round(time.perf_counter()-started,3),'ocr_fixture':{'image':'sha256:cc2b4f1e79efe9b5f274bbe4489f76d75fc685069e2f2db8f17ccee2dec0c42f','pdf_sha256':hashlib.sha256(ocr_pdf).hexdigest(),'parsed_sha256':hashlib.sha256(ocr_raw).hexdigest(),'scope':'Frozen actual OCR output plus explicit adversarial metadata mutations; synthetic content API'},'asset_sha256':{path.relative_to(ROOT/'assets').as_posix():hashlib.sha256(path.read_bytes()).hexdigest() for path in (ROOT/'assets').rglob('*') if path.is_file()},'external_requests':[path for path in network if not path.startswith(('/assets/','/v1/','/auth/')) and path!='/']}
started=time.perf_counter()
if __name__=='__main__':
 before=source_snapshot(ROOT)
 cleanup=dict(created=False,stopped=True)
 try:
  with static_server(cleanup) as origin:result=asyncio.run(run(origin))
  result.update(status='PASS_SCOPED')
 except Exception as error:
  import traceback
  result=dict(status='FAIL',failure_type=type(error).__name__,failure=str(error)[:2400],failure_stack=traceback.format_exc()[-8000:])
 result['owned_static_server_stopped']=cleanup['stopped']
 after=source_snapshot(ROOT)
 result.update(source_before=before,source_after=after,sources_unchanged=before==after)
 if before!=after or not cleanup['stopped']:result['status']='FAIL'
 out=ROOT/'evidence/research-ui'/('ui-browser-'+uuid.uuid4().hex+'.json');out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
 raise SystemExit(0 if result['status']=='PASS_SCOPED' else 1)



