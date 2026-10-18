import React, { useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Upload, FileText, Search, CheckCircle2, Circle, AlertTriangle, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "./OperationsPages";
import { mode } from '../../services/api';
import LiveLibrary from './LiveLibrary';

const LIMITS = { bytes: 2 * 1024 * 1024, pages: 100, chars: 200000 };
const STAGES = ["Bytes accepted", "Extraction / OCR", "Source spans", "Indexed", "Candidate reconciliation", "Reviewed", "Published"];
const seed = [
  { id: "doc-1", name: "DEMO_FIXTURE_rack_guide.pdf", size: "1.4 MiB", pages: 12, rev: 4, stage: 6, ocr: 92 },
  { id: "doc-2", name: "DEMO_FIXTURE_spec_sheet.pdf", size: "640 KiB", pages: 6, rev: 2, stage: 4, ocr: 98 },
  { id: "doc-3", name: "DEMO_FIXTURE_site_compliance.pdf", size: "1.9 MiB", pages: 48, rev: 1, stage: 2, ocr: 71 },
  { id: "doc-4", name: "DEMO_FIXTURE_field_report.pdf", size: "320 KiB", pages: 3, rev: 1, stage: 0, ocr: null },
];

export default function LibraryPage() {
  return mode === 'live' ? <LiveLibrary /> : <DemoLibrary />;
}

function DemoLibrary() {
  const [docs, setDocs] = useState(seed);
  const [q, setQ] = useState("");
  const [sel, setSel] = useState(seed[0].id);
  const input = useRef(null);
  const doc = docs.find((d) => d.id === sel);

  const onFile = (f) => {
    if (!f) return;
    if (f.type !== "application/pdf") return toast.error("Only PDF files are accepted");
    if (f.size > LIMITS.bytes) return toast.error(`File is ${(f.size / 1048576).toFixed(1)} MiB — limit is 2 MiB (from /v1/capabilities)`);
    const id = "local-" + Date.now();
    setDocs((d) => [{ id, name: f.name, size: `${Math.round(f.size / 1024)} KiB`, pages: "?", rev: 0, stage: -1, ocr: null, local: true }, ...d]);
    setSel(id);
    toast.message("Validated locally. Upload is BLOCKED_BACKEND in this designer build — bytes never leave your browser.");
  };

  const shown = docs.filter((d) => d.name.toLowerCase().includes(q.toLowerCase()));
  return (
    <div className="p-4 md:p-8" data-testid="library-page">
      <PageHeader title="Document Library" eyebrow="Sources · revisions · ingestion" action={
        <button onClick={() => input.current?.click()} className="n-cta h-9 px-4 flex items-center gap-2 text-xs" data-testid="library-upload-btn"><Upload size={12} />Upload PDF</button>
      }>
        Preview admission limits (snapshot): 2 MiB · 100 pages · 200,000 characters. In live mode, fetch /v1/capabilities instead of relying on these fixtures. “Indexed” does not mean reviewed or approved.
      </PageHeader>
      <input ref={input} type="file" accept="application/pdf" className="hidden" onChange={(e) => onFile(e.target.files?.[0])} data-testid="library-file-input" />

      <div className="grid grid-cols-1 xl:grid-cols-[1fr_420px] gap-6">
        <div>
          <div
            onDragOver={(e) => e.preventDefault()} onDrop={(e) => { e.preventDefault(); onFile(e.dataTransfer.files?.[0]); }}
            className="border border-dashed border-[color:var(--n-stroke-strong)] rounded-2xl p-6 mb-4 text-center text-sm text-[color:var(--n-text-mute)] hover:border-[color:var(--n-cyan)] transition-colors"
            data-testid="library-dropzone">
            <Upload size={18} className="mx-auto mb-2 text-[color:var(--n-cyan)]" /> Drop a PDF here to validate against current limits
          </div>
          <div className="relative mb-3">
            <Search size={14} className="absolute z-10 left-3 top-1/2 -translate-y-1/2 text-[color:var(--n-text-subtle)]" />
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search sources…" className="w-full h-10 pl-9 pr-3 rounded-xl n-glass text-sm outline-none" data-testid="library-search-input" />
          </div>
          <div className="n-glass rounded-2xl overflow-hidden">
            {shown.map((d) => (
              <button key={d.id} onClick={() => setSel(d.id)} className={"w-full flex items-center gap-4 px-4 py-3 text-left border-t first:border-t-0 border-[color:var(--n-stroke-soft)] transition-colors " + (d.id === sel ? "bg-[rgba(46,155,255,0.08)]" : "hover:bg-[rgba(233,239,246,0.03)]")} data-testid={`library-doc-${d.id}`}>
                <div className="w-9 h-11 rounded bg-[#F6F8FB] relative shrink-0 shadow"><div className="absolute top-0 right-0 w-3 h-3 bg-[color:var(--n-bg-inset)]" style={{ clipPath: "polygon(0 0,100% 100%,100% 0)" }} /><FileText size={14} className="absolute bottom-1.5 left-1/2 -translate-x-1/2 text-[#415072]" /></div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm truncate">{d.name}</div>
                  <div className="text-[11px] text-[color:var(--n-text-subtle)]">{d.size} · {d.pages} pages · rev {d.rev}</div>
                </div>
                <span className={"n-chip text-[10px] " + (d.local ? "n-chip-amber" : d.stage === 6 ? "n-chip-green" : "")}>{d.local ? "BLOCKED_BACKEND" : STAGES[d.stage]}</span>
              </button>
            ))}
            {!shown.length && <div className="p-6 text-sm text-center text-[color:var(--n-text-subtle)]">No sources match “{q}”.</div>}
          </div>
        </div>

        {doc && (
          <div className="n-glass rounded-2xl p-5 h-fit" data-testid="library-inspector">
            <div className="text-[10px] uppercase tracking-widest text-[color:var(--n-text-subtle)]">Ingestion journey</div>
            <div className="text-sm mt-1 mb-4 truncate">{doc.name}</div>
            <ol className="space-y-3">
              {STAGES.map((s, i) => {
                const done = i <= doc.stage, cur = i === doc.stage + 1 && !doc.local;
                return (
                  <li key={s} className="flex items-center gap-3 text-sm">
                    {done ? <CheckCircle2 size={16} className="text-[color:var(--n-green)]" /> : cur ? <Loader2 size={16} className="text-[color:var(--n-cyan)] animate-spin" /> : <Circle size={16} className="text-[color:var(--n-text-subtle)]" />}
                    <span className={done ? "" : "text-[color:var(--n-text-subtle)]"}>{s}</span>
                  </li>
                );
              })}
            </ol>
            {doc.ocr !== null && doc.ocr < 80 && <div className="mt-4 n-panel rounded-lg p-3 text-xs flex gap-2 text-[color:var(--n-amber)]"><AlertTriangle size={14} />OCR confidence {doc.ocr}% — citations from this source are flagged uncertain.</div>}
            {doc.local && <div className="mt-4 n-panel rounded-lg p-3 text-xs text-[color:var(--n-amber)]">Validated locally only. POST /v1/files is required to ingest; no upload occurred.</div>}
            {!doc.local && <Link to={`/app/documents/${doc.id}`} className="n-cta mt-5 h-10 w-full flex items-center justify-center text-xs" data-testid="library-open-doc">Open in Evidence Viewer</Link>}
          </div>
        )}
      </div>
    </div>
  );
}
