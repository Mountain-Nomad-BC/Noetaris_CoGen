import React, { useRef, useState, useEffect } from "react";
import { Link, useParams } from "react-router-dom";
import { useConversation } from "../../state/ConversationContext";
import { mode, submitChatTurn } from "../../services/api";
import { useVoice } from "../../state/VoiceContext";
import { toast } from "sonner";
import { Download, Printer, Maximize2, RotateCw, ZoomIn, ZoomOut, ChevronLeft, ChevronRight, Share2, Search, Sparkles, PanelRight, MessageSquare, BookOpen, GitCompare, ListPlus, AlertTriangle } from "lucide-react";
import { demoPdfPages, demoDoc } from "../../data/fixtures";
import LivePdfWorkspace from './LivePdfWorkspace';

const blocked = (what) => toast.message(`${what} — BLOCKED_BACKEND in this designer build`);
const PAGE_TOTAL = demoPdfPages.length;

function PaperPage({ page, flash, onSelect }) {
  const c = demoDoc.pages[page] || demoDoc.pages.default;
  return (
    <div onMouseUp={onSelect} className="w-[720px] bg-[#F6F8FB] text-[#1a2434] rounded-md shadow-[0_30px_70px_rgba(0,0,0,0.5)] p-14 relative select-text" data-testid="pdf-paper">
      <div className="absolute top-6 right-6 text-[10px] text-[#6b7a90] font-mono">DEMO_FIXTURE · page {page}/{PAGE_TOTAL}</div>
      <div className="text-xs tracking-widest text-[#415072] uppercase">Section {page}.1</div>
      <h1 className="text-3xl font-display mt-2 mb-4">{demoPdfPages[page - 1]?.title}</h1>
      <div className="h-[2px] w-24 bg-[#2E9BFF] rounded-full mb-6" />
      <p className="text-sm leading-relaxed mb-4">{c.intro}</p>
      {c.cite && (
        <p className="text-sm leading-relaxed mb-4">
          <mark className={"rounded-sm transition-shadow duration-300 " + (flash ? "shadow-[0_0_0_3px_rgba(46,155,255,0.6)]" : "")} style={{ background: "rgba(94,214,237,0.35)", color: "#0a1322" }} data-testid="pdf-citation-highlight">{c.cite}</mark>{" "}
          <span className="text-[#6b7a90]">[anchored span · server geometry]</span>
        </p>
      )}
      <div className="grid grid-cols-3 gap-3 my-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-16 rounded-md flex items-end p-2 text-[9px] font-mono text-[#6b7a90]" style={{ background: `linear-gradient(135deg, rgba(46,155,255,${0.08 + (i % 3) * 0.03}), rgba(0,0,0,0.04))` }}>fig {page}.{i + 1}</div>
        ))}
      </div>
      <p className="text-sm leading-relaxed">{c.body}</p>
      {c.ocrLow && <div className="mt-4 text-[11px] text-[#9a5b00] flex items-center gap-1"><AlertTriangle size={12} /> OCR confidence 0.68 on this region — quote coordinates unavailable, no highlight drawn.</div>}
      <div className="mt-6 text-[11px] text-[#6b7a90] font-mono">source: {demoDoc.name} · rev {demoDoc.rev}</div>
    </div>
  );
}

export default function PdfWorkspace() {
  return mode === 'live' ? <LivePdfWorkspace /> : <DemoPdfWorkspace />;
}

function DemoPdfWorkspace() {
  const [page, setPage] = useState(8);
  const [zoom, setZoom] = useState(100);
  const [rot, setRot] = useState(0);
  const [showAssistant, setShowAssistant] = useState(true);
  const [flash, setFlash] = useState(false);
  const [sel, setSel] = useState(null);
  const { id: documentId = 'doc-1' } = useParams();
  const { threads, activeId, appendMessage } = useConversation();
  const sharedMessages = threads.find(t => t.id === activeId)?.messages || [];
  const [qa, setQa] = useState([{ q: "What are the installation requirements referenced on page 8?", a: `${demoDoc.answer} [DEMO_FIXTURE]` }]);
  const [localPdf, setLocalPdf] = useState(null);
  const localInput = useRef(null);
  const localUrl = useRef(null);
  const [pending, setPending] = useState(false);
  const askController = useRef(null);
  const flashTimer = useRef(null);
  useEffect(() => () => {
    clearTimeout(flashTimer.current);
    askController.current?.abort();
    if (localUrl.current) URL.revokeObjectURL(localUrl.current);
  }, []);
  const loadLocal = (file) => {
    if (!file) return;
    if (file.type !== 'application/pdf' || file.size > 30 * 1024 * 1024) {
      toast.error('Choose a PDF of 30 MiB or less for local-only preview.'); return;
    }
    if (localUrl.current) URL.revokeObjectURL(localUrl.current);
    const url = URL.createObjectURL(file);
    localUrl.current = url;
    setLocalPdf({ url, name: file.name });
    setSel(null);
  };
  const downloadLocal = () => {
    if (!localPdf) return blocked('Download original');
    const a = document.createElement('a'); a.href = localPdf.url; a.download = localPdf.name; a.click();
  };
  const printLocal = () => {
    if (!localPdf) return blocked('Print');
    window.open(localPdf.url, '_blank', 'noopener,noreferrer');
    toast.message('Print from the browser PDF viewer in the new tab.');
  };
  const askAbout = async (question) => {
    const threadId = activeId;
    appendMessage(threadId, { id: crypto.randomUUID(), role: 'user', at: 'now', text: question, documentId });
    if (mode === 'demo') {
      const answer = 'DEMO_FIXTURE — Document-scoped question captured in your shared conversation. No backend reasoning or citations were generated.';
      appendMessage(threadId, { id: crypto.randomUUID(), role: 'assistant', at: 'now', text: answer, documentId });
      return;
    }
    askController.current?.abort();
    const controller = new AbortController();
    askController.current = controller; setPending(true);
    try {
      const answer = await submitChatTurn({ text: question, sessionId: threadId, documentId, signal: controller.signal });
      appendMessage(threadId, { id: crypto.randomUUID(), role: 'assistant', at: 'now', ...answer, documentId });
    } catch (err) {
      if (err.name !== 'AbortError') toast.error(`Document answer unavailable: ${err.message}`);
    } finally { if (askController.current === controller) setPending(false); }
  };
  const { draft: ask, setDraft: setAsk, mic } = useVoice();
  const viewRef = useRef(null);

  const jump = (p) => {
    setPage(p); setFlash(true);
    clearTimeout(flashTimer.current);
    viewRef.current?.scrollTo({ top: 0, behavior: "smooth" });
    flashTimer.current = setTimeout(() => setFlash(false), 1400);
  };
  const onSelect = () => {
    const s = window.getSelection();
    const text = s?.toString().trim();
    if (!text) return setSel(null);
    const r = s.getRangeAt(0).getBoundingClientRect();
    if (!viewRef.current || !s.rangeCount) return;
    const box = viewRef.current.getBoundingClientRect();
    setSel({ text, x: r.left - box.left + r.width / 2, y: r.top - box.top + viewRef.current.scrollTop - 48 });
  };
  const selAction = (label) => {
    if (label === "Ask about selection") askAbout(`About: “${sel.text.slice(0, 80)}”`);
    else toast.message(`${label}: “${sel.text.slice(0, 40)}…” — permission-scoped action, BLOCKED_BACKEND`);
    setSel(null); window.getSelection()?.removeAllRanges();
  };
  const submitAsk = (e) => {
    e.preventDefault();
    if (!ask.trim() || pending) return;
    askAbout(ask.trim());
    setAsk('');
  };

  if (documentId !== 'doc-1') return (
    <section className="max-w-2xl mx-auto p-8 md:p-14" role="status">
      <div className="n-glass rounded-2xl p-8">
        <h1 className="font-display text-2xl mb-3">Document preview not available</h1>
        <p className="text-sm text-[color:var(--n-text-mute)] mb-4">This designer recovery contains page fixtures only for the sample rack guide (doc-1). It does not possess the original bytes or page geometry for {documentId}. Live document viewing must load authorized bytes from GET /v1/sources/&#123;document_id&#125;/original, validate type, and render via PDF.js.</p>
        <Link to="/app/library" className="n-cta inline-flex px-5 py-3 text-sm">Return to Library</Link>
      </div>
    </section>
  );
  return (
    <div className="flex h-[calc(100dvh-64px)] min-h-[380px]" data-testid="pdf-workspace">
      {!localPdf && <aside className="w-64 shrink-0 border-r border-[color:var(--n-stroke-soft)] p-4 overflow-y-auto hidden lg:block">
        <div className="text-[10px] uppercase tracking-[0.25em] text-[color:var(--n-text-subtle)] mb-2">Document Intelligence</div>
        <div className="n-glass rounded-xl p-3 mb-4">
          <div className="text-sm truncate">{demoDoc.name}</div>
          <div className="text-[11px] text-[color:var(--n-text-subtle)]">Revision {demoDoc.rev} · {PAGE_TOTAL} pages · OCR 92%</div>
          <Link to="/app/library" className="text-[11px] text-[color:var(--n-cyan)] hover:underline">Lineage & revisions</Link>
        </div>
        <ul className="space-y-2">
          {demoPdfPages.map((p) => (
            <li key={p.page} data-testid={`pdf-thumb-${p.page}`}>
              <button type="button" onClick={() => jump(p.page)} className={"cursor-pointer p-2 rounded-lg flex items-center gap-3 transition-colors " + (p.page === page ? "bg-[rgba(46,155,255,0.08)] border border-[rgba(46,155,255,0.3)]" : "border border-transparent hover:bg-[rgba(233,239,246,0.03)]")}>
              <div className="w-11 h-14 bg-[#e9eef5] rounded-sm flex flex-col gap-1 p-1.5 shrink-0">
                <div className="h-1 w-6 bg-[#2E9BFF] rounded" />{[1, 2, 3, 4].map((i) => <div key={i} className="h-0.5 bg-[#b9c4d4] rounded" style={{ width: `${60 + ((i * p.page) % 4) * 10}%` }} />)}
              </div>
              <div className="min-w-0 text-xs">
                <div className="truncate">{p.title}</div>
                <div className="text-[color:var(--n-text-subtle)]">page {p.page}</div>
              </div>
              </button>
            </li>
          ))}
        </ul>
      </aside>}

      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        <div className="flex items-center gap-2 px-3 md:px-5 h-14 border-b border-[color:var(--n-stroke-soft)] overflow-x-auto">
          <input ref={localInput} type="file" accept="application/pdf,.pdf" className="sr-only" onChange={e => loadLocal(e.target.files?.[0])} aria-label="Select local PDF" />
          <button type="button" onClick={() => localInput.current?.click()} className="n-btn-ghost px-3 h-8 flex items-center gap-1 text-xs shrink-0">Open local PDF</button>
          {localPdf && <button type="button" onClick={() => {setLocalPdf(null); setSel(null); if (localUrl.current) URL.revokeObjectURL(localUrl.current); localUrl.current = null;}} className="n-chip shrink-0" title="Return to the demonstration document">Close local preview</button>}
          {!localPdf && <>
          <div className="flex items-center gap-1 n-glass rounded-full px-2 py-1 text-xs shrink-0">
            <button onClick={() => setZoom((z) => Math.max(50, z - 10))} className="w-7 h-7 flex items-center justify-center hover:bg-[rgba(46,155,255,0.1)] rounded-full" aria-label="Zoom out" data-testid="pdf-zoom-out-btn"><ZoomOut size={14} /></button>
            <span className="font-mono px-1" data-testid="pdf-zoom-level">{zoom}%</span>
            <button onClick={() => setZoom((z) => Math.min(200, z + 10))} className="w-7 h-7 flex items-center justify-center hover:bg-[rgba(46,155,255,0.1)] rounded-full" aria-label="Zoom in" data-testid="pdf-zoom-in-btn"><ZoomIn size={14} /></button>
          </div>
          <div className="flex items-center gap-1 n-glass rounded-full px-2 py-1 text-xs shrink-0">
            <button onClick={() => setPage((p) => Math.max(1, p - 1))} className="w-7 h-7 flex items-center justify-center hover:bg-[rgba(46,155,255,0.1)] rounded-full" aria-label="Prev page" data-testid="pdf-prev-page-btn"><ChevronLeft size={14} /></button>
            <span className="font-mono px-2" data-testid="pdf-page-indicator">{page} / {PAGE_TOTAL}</span>
            <button onClick={() => setPage((p) => Math.min(PAGE_TOTAL, p + 1))} className="w-7 h-7 flex items-center justify-center hover:bg-[rgba(46,155,255,0.1)] rounded-full" aria-label="Next page" data-testid="pdf-next-page-btn"><ChevronRight size={14} /></button>
          </div>
          <button onClick={() => setRot((r) => (r + 90) % 360)} className="n-btn-ghost w-8 h-8 flex items-center justify-center shrink-0" aria-label="Rotate" data-testid="pdf-rotate-btn"><RotateCw size={14} /></button>
          <button onClick={() => { setZoom(100); setRot(0); }} className="n-btn-ghost w-8 h-8 flex items-center justify-center shrink-0" aria-label="Fit" data-testid="pdf-fit-btn"><Maximize2 size={14} /></button>
          </>}
          <div className="ml-auto flex items-center gap-2 shrink-0">
            <button onClick={() => blocked("Share")} className="n-btn-ghost px-3 h-8 flex items-center gap-1 text-xs" data-testid="pdf-share-btn"><Share2 size={12} /> Share</button>
            <button onClick={downloadLocal} className="n-btn-ghost w-8 h-8 flex items-center justify-center" aria-label="Download" data-testid="pdf-download-btn"><Download size={14} /></button>
            <button onClick={printLocal} className="n-btn-ghost w-8 h-8 flex items-center justify-center" aria-label="Print" data-testid="pdf-print-btn"><Printer size={14} /></button>
            <button onClick={() => setShowAssistant((v) => !v)} className="n-btn-ghost w-8 h-8 flex items-center justify-center" aria-label="Toggle assistant" data-testid="pdf-assistant-toggle"><PanelRight size={14} /></button>
          </div>
        </div>

        {localPdf && <div className="px-4 py-2 text-xs text-[color:var(--n-amber)] bg-[rgba(242,179,94,.08)]" role="status">Local browser PDF preview: {localPdf.name}. Not uploaded or indexed; citation geometry, selection linking, rotation and external sharing are unavailable until backend/PDF.js integration.</div>}
        <div ref={viewRef} className="flex-1 overflow-auto p-3 md:p-10 relative" style={{ background: "radial-gradient(600px 400px at 50% 0, rgba(46,155,255,0.05), transparent 60%)" }}>
          {localPdf ? <iframe title={`Local PDF preview: ${localPdf.name}`} src={localPdf.url} className="w-full h-full min-h-[450px] rounded-xl border border-[color:var(--n-stroke-soft)]" /> : <div className="flex justify-center">
            <div style={{ transform: `scale(${zoom / 100}) rotate(${rot}deg)`, transformOrigin: "center center", transition: "transform 200ms ease", marginTop: rot % 180 ? 160 : 0, marginBottom: rot % 180 ? 160 : 0 }}>
              <PaperPage page={page} flash={flash} onSelect={onSelect} />
            </div>
          </div>}
          {sel && !localPdf && (
            <div className="absolute z-10 n-glass rounded-xl p-1 flex gap-1 -translate-x-1/2" style={{ left: sel.x, top: sel.y }} data-testid="pdf-selection-toolbar">
              {[["Ask about selection", MessageSquare], ["Explain", BookOpen], ["Compare evidence", GitCompare], ["Add to review", ListPlus]].map(([l, I]) => (
                <button key={l} onMouseDown={(e) => e.preventDefault()} onClick={() => selAction(l)} className="px-2.5 h-8 rounded-lg text-[11px] flex items-center gap-1 hover:bg-[rgba(46,155,255,0.15)] whitespace-nowrap"><I size={12} />{l}</button>
              ))}
            </div>
          )}
        </div>
      </div>

      {showAssistant && !localPdf && (
        <aside className="w-[360px] shrink-0 border-l border-[color:var(--n-stroke-soft)] p-5 overflow-y-auto hidden md:block" data-testid="pdf-assistant">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles size={14} className="text-[color:var(--n-cyan)]" />
            <div>
              <div className="text-sm">Noetaris Assistant</div>
              <div className="text-[11px] text-[color:var(--n-text-subtle)]">Same thread as Conversations · DEMO_FIXTURE</div>
            </div>
          </div>
          <div className="space-y-2 mb-4" data-testid="pdf-qa-list">
            <Link to="/app/chat" className="inline-block text-xs text-[color:var(--n-cyan)] underline">Open shared conversation</Link>
            {sharedMessages.filter(m => m.documentId === documentId).map(m => <div key={m.id} className="n-glass rounded-xl p-3 text-sm">{m.role === 'user' ? 'Question: ' : 'Response: '}{m.text}</div>)}
            {qa.map((m, i) => (
              <div key={i}>
                <div className="rounded-xl p-3 text-sm bg-[rgba(46,155,255,0.12)] border border-[rgba(46,155,255,0.3)] mb-2">{m.q}</div>
                <div className="n-glass rounded-xl p-3 text-sm">{m.a}</div>
              </div>
            ))}
          </div>
          <div className="text-[10px] uppercase tracking-widest text-[color:var(--n-text-subtle)] my-3">Key requirements</div>
          <ul className="space-y-1 text-sm">
            {demoDoc.requirements.map((k, i) => (
              <li key={k.t}><button onClick={() => jump(k.p)} className="w-full flex items-center gap-2 p-2 rounded-lg hover:bg-[rgba(46,155,255,0.05)] text-left" data-testid={`pdf-req-${i}`}>
                <span className="w-5 h-5 rounded-full border border-[color:var(--n-stroke-soft)] text-[11px] flex items-center justify-center">{i + 1}</span>
                <span className="flex-1">{k.t}</span><span className="n-chip text-[10px]">p.{k.p}</span>
              </button></li>
            ))}
          </ul>
          <div className="text-[10px] uppercase tracking-widest text-[color:var(--n-text-subtle)] my-3">Citations ({demoDoc.citations.length})</div>
          <div className="grid grid-cols-2 gap-2">
            {demoDoc.citations.map((c) => (
              <button key={c.t} onClick={() => jump(c.p)} className="n-glass rounded-lg p-2 text-[11px] text-left hover:bg-[rgba(46,155,255,0.08)]" data-testid={`pdf-citation-${c.p}`}>
                <div className="font-semibold">{c.t}</div>
                <div className="text-[color:var(--n-text-subtle)]">Page {c.p}{c.uncertain ? " · OCR uncertain" : ""}</div>
              </button>
            ))}
          </div>
          <form onSubmit={submitAsk} className="mt-5 n-glass rounded-xl p-2 flex items-center gap-2">
            <Search size={14} className="text-[color:var(--n-text-subtle)]" />
            <button type="button" onClick={() => mic.state === 'listening' ? mic.stop() : mic.start()} aria-label="Dictate document question" title="Use browser microphone" className="text-[color:var(--n-cyan)] text-xs px-1">{mic.state === 'listening' ? 'Stop mic' : 'Mic'}</button>
            <input value={ask} onChange={(e) => setAsk(e.target.value)} placeholder="Ask about this document…" className="flex-1 bg-transparent text-sm outline-none placeholder:text-[color:var(--n-text-subtle)]" data-testid="pdf-ask-input" />
            <button type="submit" disabled={pending || !ask.trim()} className="n-cta w-8 h-8 rounded-lg flex items-center justify-center" data-testid="pdf-ask-submit"><Sparkles size={12} /></button>
          </form>
        </aside>
      )}
    </div>
  );
}
