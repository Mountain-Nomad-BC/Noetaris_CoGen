import React, { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ReactFlow, Background, Controls, Handle, Position } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { PageHeader } from "./OperationsPages";
import {mode} from "../../services/api";
import LiveKnowledgeExplorer from "./LiveKnowledgeExplorer";

const STATE_COLOR = { verified: "#48C7A1", candidate: "#2E9BFF", conflicting: "#F2B35E", rejected: "#F24F61" };
const ENTITIES = [
  { id: "k1", label: "Installation clearance", state: "conflicting", src: "manual p.8 / p.12", x: 380, y: 200 },
  { id: "k2", label: "1200 mm front clearance", state: "candidate", src: "manual p.8", x: 120, y: 80 },
  { id: "k3", label: "900 mm rear clearance", state: "candidate", src: "manual p.12", x: 120, y: 330 },
  { id: "k4", label: "Dedicated 3-phase feed", state: "verified", src: "manual p.12", x: 650, y: 60 },
  { id: "k5", label: "Exhaust ventilation", state: "verified", src: "compliance p.4", x: 680, y: 330 },
  { id: "k6", label: "Level anchored floor", state: "verified", src: "manual p.8", x: 380, y: 20 },
  { id: "k7", label: "Legacy rear clearance 600 mm", state: "rejected", src: "spec r1 (superseded)", x: 380, y: 400 },
  { id: "k8", label: "Service access", state: "candidate", src: "manual p.10", x: 900, y: 200 },
];
const RELS = [["k2", "k1", "supports"], ["k3", "k1", "contradicts"], ["k6", "k1", "relates"], ["k1", "k4", "requires"], ["k1", "k5", "governed-by"], ["k7", "k1", "superseded"], ["k4", "k8", "relates"], ["k5", "k8", "relates"]];

function EntityNode({ data, selected }) {
  const c = STATE_COLOR[data.state];
  return (
    <div className="rounded-full px-4 py-2 text-xs flex items-center gap-2" style={{ background: "rgba(10,19,33,0.95)", border: `1px solid ${c}${selected ? "" : "77"}`, boxShadow: selected ? `0 0 18px ${c}66` : "none" }}>
      <Handle type="target" position={Position.Left} style={{ opacity: 0 }} />
      <span className="w-2 h-2 rounded-full" style={{ background: c }} />{data.label}
      <Handle type="source" position={Position.Right} style={{ opacity: 0 }} />
    </div>
  );
}
const nodeTypes = { entity: EntityNode };

export default function KnowledgeExplorer() {
  return mode === "live" ? <LiveKnowledgeExplorer /> : <DemoKnowledgeExplorer />;
}
function DemoKnowledgeExplorer() {
  const [states, setStates] = useState(new Set(Object.keys(STATE_COLOR)));
  const [view, setView] = useState("graph");
  const [sel, setSel] = useState("k1");
  const visible = ENTITIES.filter((e) => states.has(e.state));
  const nodes = useMemo(() => visible.map((e) => ({ id: e.id, type: "entity", position: { x: e.x, y: e.y }, data: e, selected: e.id === sel })), [visible, sel]);
  const edges = useMemo(() => RELS.filter(([a, b]) => visible.some((v) => v.id === a) && visible.some((v) => v.id === b)).map(([a, b, t]) => ({
    id: a + b, source: a, target: b, label: t, labelStyle: { fill: "#9DAEC1", fontSize: 10 }, labelBgStyle: { fill: "#0A1321" },
    style: { stroke: t === "contradicts" ? "#F2B35E" : t === "superseded" ? "#F24F61" : "rgba(46,155,255,0.5)", strokeDasharray: t === "superseded" ? "4 4" : undefined },
  })), [visible]);
  const ent = visible.find((e) => e.id === sel);
  const toggle = (s) => setStates((p) => { const n = new Set(p); n.has(s) ? n.delete(s) : n.add(s); return n; });

  return (
    <div className="p-4 md:p-8" data-testid="knowledge-page">
      <PageHeader title="Knowledge Explorer" eyebrow="Evidence graph · DEMO_FIXTURE">
        Evidence-focused network, distinct from workflow graphs. Every entity carries its source lineage and review state.
      </PageHeader>
      <div className="flex flex-wrap items-center gap-2 mb-4">
        {Object.entries(STATE_COLOR).map(([s, c]) => (
          <button key={s} onClick={() => toggle(s)} className={"n-chip text-[10px] " + (states.has(s) ? "" : "opacity-40")} style={{ color: c, borderColor: c + "66" }} data-testid={`kg-filter-${s}`}>{s}</button>
        ))}
        <div className="ml-auto flex n-glass rounded-full p-1 text-xs">
          {["graph", "list"].map((v) => <button key={v} onClick={() => setView(v)} className={"px-3 h-7 rounded-full " + (view === v ? "bg-[rgba(46,155,255,0.15)]" : "")} data-testid={`kg-view-${v}`}>{v}</button>)}
        </div>
      </div>
      <div className="grid grid-cols-1 xl:grid-cols-[1fr_340px] gap-6">
        <div className="n-glass rounded-2xl h-[540px] overflow-hidden">
          {view === "graph" ? (
            <ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes} onNodeClick={(_, n) => setSel(n.id)} fitView proOptions={{ hideAttribution: true }} nodesConnectable={false}>
              <Background color="rgba(255,255,255,0.04)" gap={24} />
              <Controls showInteractive={false} />
            </ReactFlow>
          ) : (
            <ul className="p-3 overflow-y-auto h-full">
              {visible.map((e) => (
                <li key={e.id}><button onClick={() => setSel(e.id)} className={"w-full text-left p-3 rounded-xl flex items-center gap-3 " + (e.id === sel ? "bg-[rgba(46,155,255,0.08)]" : "hover:bg-[rgba(233,239,246,0.03)]")}>
                  <span className="w-2 h-2 rounded-full" style={{ background: STATE_COLOR[e.state] }} /><span className="text-sm flex-1">{e.label}</span><span className="text-[11px] text-[color:var(--n-text-subtle)]">{e.src}</span>
                </button></li>
              ))}
            </ul>
          )}
        </div>
        {!ent && <div className="n-glass rounded-2xl p-5 h-fit text-sm text-[color:var(--n-text-subtle)]" data-testid="kg-inspector-empty">Select a visible entity to inspect its lineage.</div>}
        {ent && (
          <div className="n-glass rounded-2xl p-5 h-fit" data-testid="kg-inspector">
            <div className="text-[10px] uppercase tracking-widest" style={{ color: STATE_COLOR[ent.state] }}>{ent.state}</div>
            <div className="font-display text-xl mt-1 mb-4">{ent.label}</div>
            <div className="text-[10px] uppercase tracking-widest text-[color:var(--n-text-subtle)]">Source lineage</div>
            <div className="text-sm font-mono mb-4">{ent.src}</div>
            <div className="text-[10px] uppercase tracking-widest text-[color:var(--n-text-subtle)] mb-2">Relationships</div>
            <ul className="space-y-1 text-xs mb-4">
              {RELS.filter(([a, b]) => a === ent.id || b === ent.id).map(([a, b, t]) => (
                <li key={a + b} className="flex flex-wrap gap-x-1.5 leading-5"><span className="text-[color:var(--n-text-mute)]">{ENTITIES.find((x) => x.id === a).label}</span><span className="text-[color:var(--n-cyan)]">—{t}→</span><span className="text-[color:var(--n-text-mute)]">{ENTITIES.find((x) => x.id === b).label}</span></li>
              ))}
            </ul>
            <Link to="/app/documents/doc-1" className="n-btn-ghost h-9 w-full flex items-center justify-center text-xs" data-testid="kg-open-source">Open source evidence</Link>
          </div>
        )}
      </div>
    </div>
  );
}
