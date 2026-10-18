import assert from 'node:assert/strict';
import { test, afterEach } from 'node:test';
import { apiRequest, changeProof, submitChatTurn } from '../src/noetaris/services/liveTransport.js';
import { libraryPage, sourceRecord, uploadLimits, uploadReceipt } from '../src/noetaris/services/libraryContracts.js';
import { analysisRequest, analysisResult, accessSnapshot, shareRequest } from '../src/noetaris/services/sourceControls.js';
import { boundAnchor, containedPdfRects } from '../src/noetaris/services/pdfIdentity.js';
import { createHash } from 'node:crypto';

afterEach(() => changeProof());
test('PDF quote rectangles must be finite, nonempty and inside the visible page', () => {
  const page={left:0,top:0,right:612,bottom:792,width:612,height:792};
  const mark={left:72,top:60,right:172,bottom:74,width:100,height:14};
  assert.equal(containedPdfRects(page,[mark]),true);
  assert.equal(containedPdfRects(page,[]),false);
  for(const change of [{top:-30},{right:900},{width:0},{left:NaN}]) assert.equal(containedPdfRects(page,[{...mark,...change}]),false);
});
test('PDF citation quote identity cannot cross original, revision, page or quote hash', async () => {
  const source={id:'a'.repeat(32),revision:'1',original_sha256:'b'.repeat(64)};
  const anchor={schema:'nsai.citation-anchor/1',document_id:source.id,revision:'1',original_sha256:source.original_sha256,page:1,selector:{type:'TextQuoteSelector',exact:'Native text'},quote_sha256:createHash('sha256').update('Native text').digest('hex')};
  assert.equal(await boundAnchor(anchor,source,2),anchor);
  assert.equal(await boundAnchor(null,source,2),null);
  for(const change of [{document_id:'c'.repeat(32)},{revision:'2'},{original_sha256:'c'.repeat(64)},{page:0},{page:3},{quote_sha256:'c'.repeat(64)},{selector:{type:'TextQuoteSelector',exact:'different quote'}}])
    await assert.rejects(boundAnchor({...anchor,...change},source,2));
});
test('analysis requires explicit typed columns and binds source/request/units/coverage', () => {
  const input = { value:'2',group:'1',skip:'1',operation:'sum',unit:'USD',sheet:'' };
  const request = analysisRequest(input);
  assert.deepEqual(request,{value_column:2,group_column:1,skip_rows:1,operation:'sum',unit:'USD',sheet:null});
  for (const bad of ['','1.5','-1','1e2','101']) assert.throws(() => analysisRequest({...input,value:bad}));
  const source={id:'a'.repeat(32),revision:'1',original_sha256:'b'.repeat(64)};
  const result={schema:'nsai.table-analysis/1',method:'deterministic-decimal',provenance_complete:true,document_id:source.id,revision:'1',original_sha256:source.original_sha256,analysis_sha256:'c'.repeat(64),authority_granted:false,source_dependencies:[source.id],request,groups:[{label:'literal label',value:'0.30',included_records:2}],coverage:{total_records:4,skipped_records:1,selected_records:3,included_records:2,excluded_records:1},unit:{label:'USD'},numeric_policy:'Explicit decimals'};
  assert.equal(analysisResult(result,source,request),result);
  for (const changed of [{document_id:'d'.repeat(32)},{revision:'2'},{source_dependencies:['d'.repeat(32)]},{unit:{label:'EUR'}},{request:{...request,value_column:3}},{coverage:{...result.coverage,excluded_records:0}}])
    assert.throws(() => analysisResult({...result,...changed},source,request));
});
test('owner grants bind current epoch and preserve exact timezone/expiry precision', () => {
  const document='a'.repeat(32),owner='local-user-alice';
  const snapshot=accessSnapshot({document_id:document,owner,epoch:7,grants:[]},document,owner);
  assert.throws(() => accessSnapshot(snapshot,document,'local-user-bob'));
  const request=shareRequest(snapshot,{kind:'user',target:'local-user-bob',expiry:'2099-01-01T12:00:00.123456+02:00'});
  assert.equal(request.expected_epoch,7);assert.equal(request.expires_at,'2099-01-01T12:00:00.123456+02:00');
  for (const expiry of ['2099-02-31T12:00:00Z','2099-01-01T12:00:00','2000-01-01T12:00:00Z']) assert.throws(() => shareRequest(snapshot,{kind:'user',target:'local-user-bob',expiry}));
  assert.throws(() => shareRequest(snapshot,{kind:'user',target:'someone@example.test'}));
  assert.deepEqual(shareRequest(snapshot,{kind:'group',target:'research',revoke:true}),{expected_epoch:7,subject_kind:'group',subject_id:'research',expires_at:null,revoke:true});
});
const json = (body, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
test('same-origin canonical proofs accompany requests, not caller-selected authority', async () => {
  changeProof({ bearer: 'synthetic-test-value', csrf: 'synthetic-csrf', actor: 'local-user-alice' });
  globalThis.fetch = async (path, options) => {
    assert.equal(path, '/v1/chat'); assert.equal(options.credentials, 'same-origin'); assert.equal(options.redirect, 'error');
    assert.equal(options.headers.get('Authorization'), 'Bearer synthetic-test-value');
    assert.equal(options.headers.get('X-CSRF-Token'), 'synthetic-csrf');
    assert.equal(options.headers.get('X-NSAI-Expected-Actor'), 'local-user-alice');
    return json({ ok: true });
  };
  assert.deepEqual(await apiRequest('/v1/chat', { method: 'POST', body: {} }), { ok: true });
  await assert.rejects(apiRequest('/v1/chat', { headers: { Authorization: 'caller' } }), /managed centrally/);
});
test('authentication introspection never sends an unrelated bearer credential', async () => {
  changeProof({ bearer: 'synthetic-local' });
  globalThis.fetch = async (_, options) => { assert.equal(options.headers.has('Authorization'), false); return json({}); };
  await apiRequest('/auth/session', { auth: false });
});
test('library filters carry literal encoded path characters as data', async () => {
  for (const query of ['a%2Fb', 'source+03']) {
    globalThis.fetch = async path => { assert.equal(path, '/v1/documents?limit=25&q='+query); return json({}); };
    await apiRequest('/v1/documents?limit=25&q='+query);
  }
});
test('library/source/upload contracts cannot turn malformed results into plausible records', () => {
  const item = { id: 'a'.repeat(32), title: '<img src=x>', version: '1', sha256: 'b'.repeat(64), indexing: { state: 'queued' } };
  const valid = { items: [item], total: 1, has_more: false, next_cursor: null };
  assert.equal(libraryPage(valid), valid);
  assert.throws(() => libraryPage({ ...valid, has_more: true }), /Unrecognized/);
  assert.throws(() => libraryPage({ ...valid, items: [{ ...item, id: '../other' }] }), /Unrecognized/);
  assert.throws(() => sourceRecord({ ...item, revision: '1', raw_text: '', manifest: {}, original_sha256: item.sha256 }, 'c'.repeat(32)), /Unrecognized/);
  assert.throws(() => sourceRecord({ ...item, revision: '1', raw_text: '', manifest: [], media_type: 'text/plain', original_sha256: item.sha256 }, item.id), /Unrecognized/);
  assert.throws(() => uploadReceipt({ document_id: item.id, sha256: item.sha256, created: true }), /Unrecognized/);
  assert.throws(() => uploadLimits({ max_bytes: 1024, max_pages: 0, max_chars: 2000 }), /unavailable/);
});
test('explicit linking pins the exact existing canonical actor', async () => {
  changeProof({ actor: 'local-user-alice', csrf: 'synthetic-csrf' });
  globalThis.fetch = async (path, options) => {
    assert.equal(path, '/auth/google/start');
    assert.equal(options.headers.get('X-NSAI-Expected-Actor'), 'local-user-alice');
    assert.equal(options.headers.get('X-CSRF-Token'), 'synthetic-csrf');
    assert.deepEqual(JSON.parse(options.body), { mode: 'link' });
    return json({});
  };
  await apiRequest('/auth/google/start', { method: 'POST', body: { mode: 'link' } });
});
test('rejects external, traversal, fragment and unregistered authentication routes before transport', async () => {
  globalThis.fetch = async () => { throw new Error('Transport must not run'); };
  for (const path of ['https://attacker.test/v1/chat', '//attacker.test/v1/chat', '/v1/../auth/config', '/v1/%2e%2e/x', '/v1/chat#fragment', '/auth/unregistered', '/v1/a\\b'])
    await assert.rejects(apiRequest(path), /Rejected API path/);
});
test('late response cannot cross an identity epoch even if fetch ignores abort', async () => {
  let finish;
  globalThis.fetch = async () => await new Promise(resolve => { finish = resolve; });
  const pending = apiRequest('/v1/documents');
  changeProof({ actor: 'local-user-bob' }); finish(json({ documents: ['private-alice'] }));
  await assert.rejects(pending, error => error.name === 'AbortError');
});
test('caller cancellation rejects a response even if underlying transport resolves', async () => {
  const controller = new AbortController();
  globalThis.fetch = async () => { controller.abort(); return json({ private: true }); };
  await assert.rejects(apiRequest('/v1/documents', { signal: controller.signal }), error => error.name === 'AbortError');
});
test('multipart upload leaves content boundary to the browser', async () => {
  const form = new FormData(); form.set('version', '1');
  globalThis.fetch = async (_, options) => { assert.equal(options.body, form); assert.equal(options.headers.has('Content-Type'), false); return json({}); };
  await apiRequest('/v1/files', { method: 'POST', body: form });
});
test('malformed JSON and an SPA fallback cannot look like successful API results', async () => {
  globalThis.fetch = async () => new Response('{', { headers: { 'Content-Type': 'application/json' } });
  await assert.rejects(apiRequest('/v1/documents'), /malformed JSON/);
  globalThis.fetch = async () => new Response('<html>SPA</html>', { headers: { 'Content-Type': 'text/html' } });
  await assert.rejects(apiRequest('/v1/documents'), /Expected a JSON/);
});
test('original bytes download is bounded and cannot substitute an arbitrary route', async () => {
  const path = '/v1/sources/'+'a'.repeat(32)+'/original';
  globalThis.fetch = async () => new Response(new Uint8Array([0, 255, 13, 10]), { headers: { 'Content-Type': 'application/pdf' } });
  const result = await apiRequest(path, { responseType: 'bytes', maximumBytes: 4 });
  assert.deepEqual([...result.bytes], [0, 255, 13, 10]);
  await assert.rejects(apiRequest(path, { responseType: 'bytes', maximumBytes: 3 }), /byte budget/);
  await assert.rejects(apiRequest('/v1/documents', { responseType: 'bytes', maximumBytes: 4 }), /original-source route/);
});
test('non-string validation errors are rendered as a safe HTTP status', async () => {
  globalThis.fetch = async () => json({ detail: [{ input: 'sensitive input' }] }, 422);
  await assert.rejects(apiRequest('/v1/chat'), error => error.status === 422 && !error.message.includes('sensitive'));
});
test('expired authenticated requests request a fresh identity without sending response content in events', async () => {
  const original = globalThis.dispatchEvent;
  const events = [];
  globalThis.dispatchEvent = event => { events.push(event.type); return true; };
  try {
    changeProof({ actor: 'local-user-alice' });
    globalThis.fetch = async () => json({ detail: 'Unauthorized' }, 401);
    await assert.rejects(apiRequest('/v1/documents'), error => error.status === 401);
    assert.deepEqual(events, ['noetaris-auth-expired']);
    await assert.rejects(apiRequest('/auth/session', { auth: false }), error => error.status === 401);
    assert.deepEqual(events, ['noetaris-auth-expired']);
  } finally {
    if (original === undefined) delete globalThis.dispatchEvent;
    else globalThis.dispatchEvent = original;
  }
});
test('chat maps real question/source DTO and requires backend session identity', async () => {
  globalThis.fetch = async (_, options) => {
    assert.deepEqual(JSON.parse(options.body), { question: 'Evidence?', document_ids: ['a'.repeat(32)] });
    return json({ answer: 'Supported excerpt', citations: [], session_id: 'b'.repeat(32) });
  };
  const reply = await submitChatTurn({ text: 'Evidence?', sessionId: 'local-preview', documentId: 'a'.repeat(32) });
  assert.equal(reply.sessionId, 'b'.repeat(32));
  globalThis.fetch = async () => json({ response: { text: 'unmapped plausible answer' } });
  await assert.rejects(submitChatTurn({ text: 'Evidence?' }), /Unrecognized/);
});
