import React, { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Pause, Play, Download, Search, ChevronRight } from "lucide-react";
import { PageHeader } from "./OperationsPages";

const LEVELS = ["DEBUG", "INFO", "WARN", "ERROR"];
const LEVEL_COLOR = { DEBUG: "var(--n-text-subtle)", INFO: "var(--n-cyan)", WARN: "var(--n-amber)", ERROR: "var(--n-red)" };
const NODES = ["n1 trigger", "n2 source-index", "n3 ocr", "n4 research-agent", "n5 policy-check", "n6 branch", "n7 publish"];
const MSGS = [
  ["INFO", "node started"], ["DEBUG", "reserved budget 0.004 USD"], ["INFO", "citation span resolved p.8"],
  ["WARN", "OCR confidence 0.71 below 0.80 threshold"], ["INFO", "node completed"], ["ERROR", "provider timeout after 30s — retry 1/3 queued"],
  ["DEBUG", "cache hit index v12"], ["INFO", "policy SOURCE_SCOPE_VERIFIED"],
];

export const RUNS = [
  { id: "run-4821", wf: "wf-sample r37", status: "running", started: "2m ago", dur: "—", cost: "$0.42" },
  { id: "run-4820", wf: "wf-sample r37", status: "failed", started: "41m ago", dur: "1m 12s", cost: "$0.18" },
  { id: "run-4819", wf: "Evidence pipeline r5", status: "succeeded", started: "1h ago", dur: "4m 03s", cost: "$1.06" },
  { id: "run-4818", wf: "Research digest r2", status: "unknown", started: "3h ago", dur: "—", cost: "reserved" },
  { id: "run-4817", wf: "wf-sample r36", status: "succeeded", started: "5h ago", dur: "2m 44s", cost: "$0.39" },
];
const tone = { running: "", failed: "n-chip-red", succeeded: "n-chip-green", unknown: "n-chip-amber" };

let seq = 0;
const makeLine = () => {
  const [level, msg] = MSGS[Math.floor(Math.random() * MSGS.length)];
  return { id: ++seq, at: new Date(), level, node: NODES[Math.floor(Math.random() * NODES.length)], msg };
};

export function LogViewer({ height = "h-[420px]" }) {
  const [lines, setLines] = useState(() => Array.from({ length: 40 }, makeLine));
  const [paused, setPaused] = useState(false);
  const [levels, setLevels] = useState(new Set(LEVELS));
  const [q, setQ] = useState("");
  const box = useRef(null);

  useEffect(() => {
    if (paused) return;
    const t = setInterval(() => setLines((l) => [...l.slice(-499), makeLine()]), 900);
    return () => clearInterval(t);
  }, [paused]);
  const stick = useRef(true);
  useEffect(() => { if (!paused && stick.current && box.current) box.current.scrollTop = box.current.scrollHeight; }, [lines, paused]);

  const shown = useMemo(() => lines.filter((l) => levels.has(l.level) && (l.msg + l.node).toLowerCase().includes(q.toLowerCase())), [lines, levels, q]);
  const toggle = (lv) => setLevels((s) => { const n = new Set(s); n.has(lv) ? n.delete(lv) : n.add(lv); return n; });
  const exportLog = () => {
    const blob = new Blob([shown.map((l) => `${l.at.toISOString()} ${l.level} [${l.node}] ${l.msg}`).join("\n")], { type: "text/plain" });
    const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "noetaris-demo-log.txt"; a.click();
  };

  return (
    <div className="n-glass rounded-2xl p-4" data-testid="log-viewer">
      <div className="flex flex-wrap items-center gap-2 mb-3">
        <div className="text-[11px] uppercase tracking-widest text-[color:var(--n-text-subtle)] mr-2">Live tail · DEMO_FIXTURE stream</div>
        {LEVELS.map((lv) => (
          <button key={lv} onClick={() => toggle(lv)} className={"n-chip text-[10px] " + (levels.has(lv) ? "" : "opacity-40")} style={{ color: LEVEL_COLOR[lv] }} data-testid={`log-level-${lv.toLowerCase()}`}>{lv}</button>
        ))}
        <div className="relative ml-auto">
          <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[color:var(--n-text-subtle)]" />
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Filter logs…" className="h-8 pl-7 pr-3 rounded-lg n-panel text-xs outline-none w-52" data-testid="log-search-input" />
        </div>
        <button onClick={() => setPaused((p) => !p)} className="n-btn-ghost h-8 px-3 text-xs flex items-center gap-1" data-testid="log-pause-btn">{paused ? <Play size={12} /> : <Pause size={12} />}{paused ? "Resume" : "Pause"}</button>
        <button onClick={exportLog} className="n-btn-ghost h-8 px-3 text-xs flex items-center gap-1" data-testid="log-export-btn"><Download size={12} />Export</button>
      </div>
      <div ref={box} onScroll={(e) => { const el = e.currentTarget; stick.current = el.scrollHeight - el.scrollTop - el.clientHeight < 40; }} className={`font-mono text-[12px] leading-6 overflow-y-auto ${height} rounded-lg p-3`} style={{ background: "rgba(3,7,14,0.7)" }}>
        {shown.map((l) => (
          <div key={l.id} className="flex gap-3 hover:bg-[rgba(46,155,255,0.05)] px-1 rounded">
            <span className="text-[color:var(--n-text-subtle)] shrink-0">{l.at.toLocaleTimeString()}</span>
            <span className="w-12 shrink-0" style={{ color: LEVEL_COLOR[l.level] }}>{l.level}</span>
            <span className="text-[color:var(--n-violet)] shrink-0 w-36 truncate">[{l.node}]</span>
            <span className="text-[color:var(--n-text)]">{l.msg}</span>
          </div>
        ))}
        {!shown.length && <div className="text-[color:var(--n-text-subtle)]">No lines match the current filter.</div>}
      </div>
      <div className="text-[11px] text-[color:var(--n-text-subtle)] mt-2">{shown.length} of {lines.length} lines · {paused ? "paused" : "streaming"} · Live source: GET /v1/executions/{"{id}"}/events (PENDING_BACKEND)</div>
    </div>
  );
}

export default function ExecutionsPage() {
  const { id } = useParams();
  const [sel, setSel] = useState(id || RUNS[0].id);
  useEffect(() => { if (id) setSel(id); }, [id]);
  const nav = useNavigate();
  const pick = (rid) => (id ? nav(`/app/executions/${rid}`) : setSel(rid));
  const run = RUNS.find((r) => r.id === sel) || RUNS[0];
  return (
    <div className="p-4 md:p-8" data-testid="executions-page">
      <PageHeader title={id ? `Execution ${sel}` : "Executions / Debugger"} eyebrow="Runs · traces · logs">
        Run list, node-level trace and log viewer. Unknown outcomes stay reserved — never shown as success.
      </PageHeader>
      <div className="grid grid-cols-1 xl:grid-cols-[380px_1fr] gap-6">
        <div className="n-glass rounded-2xl p-3 h-fit">
          {RUNS.map((r) => (
            <button key={r.id} onClick={() => pick(r.id)} className={"w-full text-left p-3 rounded-xl flex items-center gap-3 transition-colors " + (r.id === sel ? "bg-[rgba(46,155,255,0.1)] border border-[rgba(46,155,255,0.3)]" : "border border-transparent hover:bg-[rgba(233,239,246,0.03)]")} data-testid={`run-${r.id}`}>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-mono">{r.id}</div>
                <div className="text-[11px] text-[color:var(--n-text-subtle)]">{r.wf} · {r.started}</div>
              </div>
              <span className={"n-chip text-[10px] " + tone[r.status]}>{r.status}</span>
              <ChevronRight size={14} className="text-[color:var(--n-text-subtle)]" />
            </button>
          ))}
        </div>
        <div className="space-y-6 min-w-0">
          <div className="n-glass rounded-2xl p-5">
            <div className="flex items-center gap-3 mb-4">
              <div className="font-display text-xl font-mono">{run.id}</div>
              <span className={"n-chip " + tone[run.status]}>{run.status}</span>
              <Link to="/app/workflows/wf-sample/edit" className="ml-auto text-xs text-[color:var(--n-cyan)] hover:underline">Open in Studio</Link>
            </div>
            <div className="grid grid-cols-4 gap-3 mb-5">
              {[["Workflow", run.wf], ["Duration", run.dur], ["Cost", run.cost], ["Started", run.started]].map(([k, v]) => (
                <div key={k} className="n-panel rounded-lg p-3"><div className="text-[10px] uppercase tracking-widest text-[color:var(--n-text-subtle)]">{k}</div><div className="text-sm mt-1">{v}</div></div>
              ))}
            </div>
            <div className="flex items-center gap-1 overflow-x-auto pb-1">
              {NODES.map((n, i) => {
                const st = run.status === "failed" && i === 3 ? "err" : run.status === "running" && i === 3 ? "act" : run.status === "unknown" && i >= 4 ? "unk" : (run.status === "running" && i > 3) || (run.status === "failed" && i > 3) ? "pend" : "ok";
                const c = { ok: "var(--n-green)", err: "var(--n-red)", act: "var(--n-cyan)", unk: "var(--n-amber)", pend: "var(--n-text-subtle)" }[st];
                return (
                  <React.Fragment key={n}>
                    <div className="n-panel rounded-lg px-3 py-2 min-w-[120px]" style={{ borderColor: c }}>
                      <div className="text-[10px] font-mono" style={{ color: c }}>{n.split(" ")[0]} · {st}</div>
                      <div className="text-xs truncate">{n.split(" ")[1]}</div>
                    </div>
                    {i < NODES.length - 1 && <div className="w-4 h-px shrink-0" style={{ background: c }} />}
                  </React.Fragment>
                );
              })}
            </div>
          </div>
          <LogViewer />
        </div>
      </div>
    </div>
  );
}
