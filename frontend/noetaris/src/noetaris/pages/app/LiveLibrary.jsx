import React, { useEffect, useRef, useState } from 'react';
import { uploadWarning, uploadAcknowledgmentVersion } from '../../content/publicDocuments';
import { apiRequest } from '../../services/api';
import { libraryPage, sourceId, sourceRecord, uploadLimits, uploadReceipt } from '../../services/libraryContracts';
import { useAuth } from '../../state/AuthContext';
import SourceAnalysis from '../../components/SourceAnalysis';
import LibraryKnowledgeSearch from '../../components/LibraryKnowledgeSearch';
import SourceSharing from '../../components/SourceSharing';
import { Link,useLocation } from 'react-router-dom';
import { useLiveChat } from '../../state/LiveChatContext';

const describe = error => error.requestId ? `${error.message} (request ${error.requestId})` : error.message;
export default function LiveLibrary() {
  const auth = useAuth();
  const chat=useLiveChat();const location=useLocation();
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState('');
  const [cursor, setCursor] = useState(null);
  const [reload, setReload] = useState(0);
  const [page, setPage] = useState({ status: 'loading', data: null, error: null });
  const [selected, setSelected] = useState(()=>sourceId(location.state?.documentId)?location.state.documentId:null);
  const [source, setSource] = useState({ status: 'empty', data: null, error: null });
  const [sourceReload, setSourceReload] = useState(0);
  const [upload, setUpload] = useState({ status: 'idle', receipt: null, error: null });
  const [version, setVersion] = useState('1');
  const [uploadAcknowledged, setUploadAcknowledged] = useState(false);
  useEffect(() => setUploadAcknowledged(false), [auth.identity.actor]);
  const [download, setDownload] = useState({ busy: false, error: null });
  const fileInput = useRef(null);
  const uploadController = useRef(null);
  const downloadController = useRef(null);
  const urls = useRef(new Set());
  let limits;
  try { limits = uploadLimits(auth.capabilities?.upload_limits); } catch { limits = null; }
  const canUpload = auth.identity.permissions?.includes('ingest') && !!limits;
  useEffect(() => {
    const controller = new AbortController(); let alive = true;
    setPage({ status: 'loading', data: null, error: null });
    const params = new URLSearchParams({ limit: '25', ...(filter ? { q: filter } : {}), ...(cursor ? { cursor } : {}) });
    apiRequest(`/v1/documents?${params}`, { signal: controller.signal }).then(libraryPage).then(data => {
      if (alive) setPage({ status: data.items.length ? 'ready' : 'empty', data, error: null });
    }).catch(error => { if (alive && error.name !== 'AbortError') setPage({ status: error.status === 403 ? 'forbidden' : 'error', data: null, error: describe(error) }); });
    return () => { alive = false; controller.abort(); };
  }, [filter, cursor, reload, auth.identity.actor]);
  useEffect(() => {
    downloadController.current?.abort(); setDownload({ busy: false, error: null });
    const controller = new AbortController(); let alive = true; let timer; let polls = 0;
    setSource({ status: selected ? 'loading' : 'empty', data: null, error: null });
    async function refreshSource() {
      try {
        const data = sourceRecord(await apiRequest(`/v1/sources/${selected}`, { signal: controller.signal }), selected);
        if (!alive) return;
        setSource({ status: 'ready', data, error: null });
        if (['queued', 'running'].includes(data.indexing.state) && polls++ < 120) {
          timer = setTimeout(refreshSource, 1500);
        } else if (data.indexing.state === 'ready') {
          setPage(current => current.data ? { ...current, data: { ...current.data, items: current.data.items.map(item => item.id === selected ? { ...item, indexing: data.indexing } : item) } } : current);
        }
      } catch (error) {
        if (alive && error.name !== 'AbortError') setSource({ status: error.status === 403 ? 'forbidden' : 'error', data: null, error: describe(error) });
      }
    }
    if (selected) refreshSource();
    return () => { alive = false; clearTimeout(timer); controller.abort(); };
  }, [selected, sourceReload, auth.identity.actor]);
  useEffect(() => () => {
    uploadController.current?.abort(); downloadController.current?.abort();
    for (const url of urls.current) URL.revokeObjectURL(url);
    urls.current.clear();
  }, []);
  async function ingest(file) {
    if (!file || !canUpload || !uploadAcknowledged || upload.status === 'running') return;
    if (file.size < 1 || file.size > limits.max_bytes) {
      if (fileInput.current) fileInput.current.value = '';
      setUpload({ status: 'error', receipt: null, error: `Choose a nonempty file at most ${limits.max_bytes} bytes.` }); return;
    }
    if (!version.trim() || version.length > 50) {
      if (fileInput.current) fileInput.current.value = '';
      setUpload({ status: 'error', receipt: null, error: 'Source revision must contain 1–50 characters.' }); return;
    }
    const controller = new AbortController(); uploadController.current = controller;
    setUpload({ status: 'running', receipt: null, error: null });
    try {
      const form = new FormData(); form.set('file', file); form.set('version', version); form.set('upload_ack', uploadAcknowledgmentVersion);
      const receipt = uploadReceipt(await apiRequest('/v1/files', { method: 'POST', body: form, signal: controller.signal }));
      if (controller.signal.aborted) return;
      setUpload({ status: 'ready', receipt, error: null }); setSelected(receipt.document_id); setSourceReload(value => value + 1);
      setCursor(null); setReload(value => value + 1);
    } catch (error) {
      if (!controller.signal.aborted) setUpload({ status: 'error', receipt: null, error: describe(error) });
    } finally {
      if (fileInput.current) fileInput.current.value = '';
      if (uploadController.current === controller) uploadController.current = null;
    }
  }
  async function downloadOriginal() {
    const current = source.data;
    if (!current?.original_sha256 || download.busy) return;
    const controller = new AbortController(); downloadController.current = controller;
    setDownload({ busy: true, error: null });
    try {
      const payload = await apiRequest(`/v1/sources/${current.id}/original`, { signal: controller.signal, responseType: 'bytes', maximumBytes: 32 * 1024 * 1024 });
      const hash = [...new Uint8Array(await crypto.subtle.digest('SHA-256', payload.bytes))].map(value => value.toString(16).padStart(2, '0')).join('');
      if (hash !== current.original_sha256) throw new Error('Original-byte integrity check failed; download withheld.');
      if (controller.signal.aborted) return;
      const url = URL.createObjectURL(new Blob([payload.bytes], { type: 'application/octet-stream' })); urls.current.add(url);
      const link = document.createElement('a'); link.href = url; link.download = `${current.id}.original`; link.click();
      setTimeout(() => { URL.revokeObjectURL(url); urls.current.delete(url); }, 1000);
      setDownload({ busy: false, error: null });
    } catch (error) { if (!controller.signal.aborted) setDownload({ busy: false, error: describe(error) }); }
  }
  return <div className="p-4 md:p-8 space-y-6" data-testid="live-library">
    <h1 className="font-display text-2xl">Document library</h1>
    <p>Authorized sources from the backend. Indexing is separate from review and factual approval.</p>
    <section className="n-glass rounded-xl p-4 space-y-3" aria-label="Upload source">
      <div className="n-panel p-4 rounded-lg space-y-2" role="note" aria-label="Experimental upload restrictions">{uploadWarning.map(line => <p key={line}>{line}</p>)}</div>
      <label className="flex gap-3 items-start"><input type="checkbox" data-testid="upload-restrictions-ack" checked={uploadAcknowledged} onChange={event => setUploadAcknowledged(event.target.checked)} disabled={upload.status === 'running'} /><span>I am 18 or older, have read the <Link className="underline" to="/terms">Terms</Link> and <Link className="underline" to="/privacy">Privacy notice</Link>, and confirm this document is publicly available, non-sensitive, and legally authorized for processing. I understand the experimental-use restrictions.</span></label>
      <p>{limits ? `Server limits: ${limits.max_bytes} bytes · ${limits.max_pages} PDF pages · ${limits.max_chars} extracted characters.` : 'Upload limits unavailable; upload disabled.'}</p>
      <p>Supported: TXT, Markdown, CSV, TSV, JSON, bounded XLSX and PDF. The parser validates the entire admitted source.</p>
      <label className="block">Source revision <input value={version} maxLength={50} onChange={event => setVersion(event.target.value)} disabled={!canUpload || upload.status === 'running'} className="n-panel rounded p-2 ml-2" /></label>
      <input ref={fileInput} type="file" className="block w-full min-w-0 max-w-full" accept=".txt,.md,.csv,.tsv,.json,.xlsx,.pdf" aria-label="Upload source file" data-testid="live-upload-input"
        disabled={!canUpload || !uploadAcknowledged || upload.status === 'running'} onChange={event => ingest(event.target.files?.[0])} />
      {!canUpload && <p>Ingestion is unavailable for this identity or configuration.</p>}
      {upload.status === 'running' && <p role="status">Submitting source. Publication is not confirmed yet.</p>}
      {upload.error && <p role="alert">{upload.error}</p>}
      {upload.receipt && <p role="status" className="break-all" data-testid="live-upload-receipt">{upload.receipt.created ? 'Stored' : 'Existing source retained'}: {upload.receipt.document_id} · initial indexing: {upload.receipt.indexing.state}</p>}
      {upload.receipt&&source.data?.id===upload.receipt.document_id&&<p role="status" data-testid="upload-processing-status">Current indexing: {source.data.indexing.state}. {source.data.indexing.state==='ready'?'Ready for source-grounded questions.':source.data.indexing.state==='failed'?'Indexing failed. Inspect the queue before querying this source.':'Processing status updates automatically while this source is selected.'}</p>}
    </section>
    <LibraryKnowledgeSearch onSelect={setSelected} />
    <form className="flex flex-wrap gap-3" onSubmit={event => { event.preventDefault(); setFilter(query.trim()); setCursor(null); setSelected(null); setReload(value => value + 1); }}>
      <label>Filter titles <input type="search" maxLength={200} value={query} onChange={event => setQuery(event.target.value)} className="n-panel rounded p-2 ml-2" data-testid="live-library-filter" /></label>
      <button className="n-cta rounded px-4 py-2" type="submit">Search library</button>
      <button className="n-btn-ghost rounded px-4 py-2" type="button" onClick={() => { setCursor(null); setReload(value => value + 1); }}>Refresh library</button>
    </form>
    {page.error && <p role="alert">{page.error}</p>}
    {page.status === 'loading' && <p role="status">Loading authorized sources…</p>}
    {page.status === 'empty' && <p role="status">No authorized sources match this filter.</p>}
    {page.data && <>
      <p data-testid="live-library-total">{page.data.total} matching sources. Pages reflect current data, not a frozen snapshot.</p>
      <ul className="space-y-2" data-testid="live-library-items">{page.data.items.map(item => <li key={item.id}>
        <button className="n-glass rounded-xl p-4 w-full text-left break-words" data-source-id={item.id} onClick={() => setSelected(item.id)}>
          <strong>{item.title}</strong><span className="block text-sm">revision {item.version} · indexing: {item.indexing.state}</span>
        </button>
      </li>)}</ul>
      <div className="flex gap-3"><button disabled={!cursor || page.status === 'loading'} onClick={() => setCursor(null)}>First page</button>
        <button data-testid="live-library-next" disabled={!page.data.has_more || page.status === 'loading'} onClick={() => { setCursor(page.data.next_cursor); setSelected(null); }}>Next page</button></div>
    </>}
    {selected && <section className="n-glass rounded-xl p-4 space-y-3" aria-label="Source inspector" data-testid="live-source-inspector">
      <h2 className="font-display text-xl">Source evidence</h2>
      {source.status === 'loading' && <p role="status">Loading current source authorization and evidence…</p>}
      {source.error && <p role="alert">{source.error}</p>}
      {source.data && <>
        <h3>{source.data.title}</h3>
        <p className="break-all">{source.data.id} · revision {source.data.revision} · {source.data.media_type || 'media type unavailable'}</p>
        <Link className="n-btn-ghost inline-flex p-2" to={`/app/knowledge?source=${source.data.id}`} data-testid="browse-live-knowledge">Browse source knowledge</Link>
          <p>Current indexing: <span data-testid="live-source-index-state">{source.data.indexing.state}</span></p>
        {auth.identity.permissions?.includes('chat')&&<Link className="n-btn-ghost inline-flex p-2" to="/app/chat" onClick={()=>chat.store.chooseSource(source.data.id,source.data.revision)} data-testid="ask-live-source">Ask about this source</Link>}
        {source.data.media_type === 'application/pdf' && <Link className="n-cta inline-flex p-2 rounded" to={`/app/documents/${source.data.id}`} data-testid="open-live-pdf">Open verified PDF workspace</Link>}
        <p className="break-all">Original SHA-256: {source.data.original_sha256 || 'Original hash unavailable'}</p>
        <button className="n-btn-ghost p-2" onClick={() => setSourceReload(value => value + 1)}>Refresh source state</button>
        <button className="n-cta p-2 rounded" disabled={!source.data.original_sha256 || download.busy} onClick={downloadOriginal} data-testid="live-download-original">Download verified original</button>
        <p className="text-sm">Original download safety bound: 32 MiB; lowering new-upload limits does not change retained source bytes.</p>
        {download.error && <p role="alert">{download.error}</p>}
        <details><summary>Extracted-text preview (first 8,000 characters)</summary><pre className="whitespace-pre-wrap break-words">{source.data.raw_text.slice(0, 8000)}</pre></details>
        <details><summary>Stored evidence manifest preview (first 20,000 characters)</summary><pre className="whitespace-pre-wrap break-words" data-testid="live-source-manifest">{JSON.stringify(source.data.manifest, null, 2).slice(0, 20000)}</pre></details>
        <p>Preview bounds do not alter stored originals or manifests. Geometry, OCR accuracy and factual review are separate qualifications.</p>
        <SourceAnalysis key={`analysis:${source.data.id}:${source.data.revision}`} source={source.data} />
        <SourceSharing key={`sharing:${source.data.id}:${source.data.revision}`} source={source.data} identity={auth.identity} />
      </>}
    </section>}
  </div>;
}
