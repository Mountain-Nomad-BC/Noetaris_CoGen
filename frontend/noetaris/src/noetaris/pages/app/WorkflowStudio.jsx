import React, { useCallback, useRef, useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import {
  ReactFlow, Background, Controls, MiniMap, Handle, Position,
  applyNodeChanges, applyEdgeChanges, addEdge, MarkerType,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { toast } from "sonner";
import { Hexagon, Database, Bot, GitBranch, Shield, FileCheck2, Play, Save, Undo2, Redo2, Sparkles, Settings, Trash2, Check, X, AlertTriangle, CheckCircle2 } from "lucide-react";

const palette = [
  { kind: "trigger", icon: Play, color: "#5ED6ED", label: "Trigger" },
  { kind: "data", icon: Database, color: "#2E9BFF", label: "Data source" },
  { kind: "agent", icon: Bot, color: "#8F85E8", label: "Agent" },
  { kind: "branch", icon: GitBranch, color: "#F2B35E", label: "Branch" },
  { kind: "govern", icon: Shield, color: "#F24F61", label: "Governance" },
  { kind: "output", icon: FileCheck2, color: "#48C7A1", label: "Output" },
];
const kindOf = (k) => palette.find((p) => p.kind === k) || palette[0];
const arrow = (c) => ({ type: MarkerType.ArrowClosed, color: c });

function TypedNode({ data, selected }) {
  const { label, kind, status, diff } = data;
  const { icon: Icon = Hexagon, color } = kindOf(kind);
  const ring = diff === "add" ? "#48C7A1" : diff === "edit" ? "#F2B35E" : color;
  return (
    <div className="rounded-xl p-3 min-w-[200px] relative transition-shadow"
      style={{ background: "linear-gradient(180deg, rgba(16,30,48,0.98), rgba(10,19,33,0.98))",
        border: `1px ${diff ? "dashed" : "solid"} ${ring}${selected ? "" : "88"}`,
        boxShadow: status === "active" ? `0 0 24px ${color}66` : selected ? `0 0 0 2px ${color}55` : "0 4px 20px rgba(0,0,0,0.4)" }}>
      <Handle type="target" position={Position.Left} style={{ background: color }} />
      <div className="flex items-center gap-2 mb-1">
        <div className="w-7 h-7 rounded-md flex items-center justify-center" style={{ background: color + "22", border: `1px solid ${color}66` }}>
          <Icon size={14} color={color} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-[10px] uppercase tracking-widest" style={{ color }}>{kind}</div>
          <div className="text-sm truncate">{label}</div>
        </div>
      </div>
      <div className="flex items-center gap-2 text-[11px] mt-2">
        <span className="n-chip" style={{ color, borderColor: color + "66", background: color + "11" }}>{status || "ready"}</span>
        {diff && <span className="n-chip n-chip-green">AI {diff}</span>}
      </div>
      <Handle type="source" position={Position.Right} style={{ background: color }} />
    </div>
  );
}
const nodeTypes = { typed: TypedNode };

const mk = (id, x, y, label, kind, status = "ready") => ({ id, type: "typed", position: { x, y }, data: { label, kind, status } });
const initialNodes = [
  mk("n1", 40, 160, "Document upload", "trigger"),
  mk("n2", 300, 60, "Source index", "data"),
  mk("n3", 300, 260, "OCR extraction", "data", "active"),
  mk("n4", 580, 160, "Research agent", "agent"),
  mk("n5", 860, 60, "Policy check", "govern"),
  mk("n6", 860, 260, "Branch quality", "branch"),
  mk("n7", 1140, 160, "Publish evidence", "output"),
];
const ed = (id, s, t, c, animated = false) => ({ id, source: s, target: t, animated, markerEnd: arrow(c) });
const initialEdges = [
  ed("e1", "n1", "n2", "#2E9BFF", true), ed("e2", "n1", "n3", "#2E9BFF", true),
  ed("e3", "n2", "n4", "#8F85E8"), ed("e4", "n3", "n4", "#8F85E8"),
  ed("e5", "n4", "n5", "#F24F61"), ed("e6", "n4", "n6", "#F2B35E"),
  ed("e7", "n5", "n7", "#48C7A1"), ed("e8", "n6", "n7", "#48C7A1"),
];

function validate(nodes, edges) {
  const issues = [];
  nodes.forEach((n) => {
    const inc = edges.some((e) => e.target === n.id);
    const out = edges.some((e) => e.source === n.id);
    if (n.data.kind !== "trigger" && !inc) issues.push(`${n.data.label}: no input connection`);
    if (n.data.kind !== "output" && !out) issues.push(`${n.data.label}: no output connection`);
  });
  if (!nodes.some((n) => n.data.kind === "govern")) issues.push("Workflow has no governance node");
  return issues;
}

export default function WorkflowStudio() {
  const { id = "new" } = useParams();
  const DRAFT_KEY = `noetaris.workflow.${id}.draft`;
  const blank = id === "new" ? { nodes: [mk("n1", 80, 160, "Start", "trigger", "draft")], edges: [] } : { nodes: initialNodes, edges: initialEdges };
  const [hasSaved, setHasSaved] = useState(() => !!localStorage.getItem(DRAFT_KEY));
  const [graph, setGraph] = useState(() => { try { return JSON.parse(localStorage.getItem(DRAFT_KEY)) || blank; } catch { return blank; } });
  const [past, setPast] = useState([]);
  const [future, setFuture] = useState([]);
  const [selectedId, setSelectedId] = useState("n4");
  const [dirty, setDirty] = useState(false);
  const [issues, setIssues] = useState(null);
  const [proposal, setProposal] = useState(null);
  const rf = useRef(null);
  const { nodes, edges } = graph;

  const commit = useCallback((next) => {
    setPast((p) => [...p.slice(-49), graph]);
    setFuture([]);
    setGraph(next);
    setDirty(true);
  }, [graph]);

  const onNodesChange = useCallback((changes) => {
    const structural = changes.some((c) => c.type === "remove" || (c.type === "position" && c.dragging === false));
    const next = { ...graph, nodes: applyNodeChanges(changes, graph.nodes) };
    structural ? commit(next) : setGraph(next);
  }, [graph, commit]);
  const onEdgesChange = useCallback((changes) => {
    const next = { ...graph, edges: applyEdgeChanges(changes, graph.edges) };
    changes.some((c) => c.type === "remove") ? commit(next) : setGraph(next);
  }, [graph, commit]);
  const onConnect = useCallback((p) => {
    const src = nodes.find((n) => n.id === p.source);
    const tgt = nodes.find((n) => n.id === p.target);
    if (tgt?.data.kind === "trigger") { toast.error("Incompatible port: triggers cannot receive input"); return; }
    if (src?.data.kind === "output") { toast.error("Incompatible port: outputs are terminal"); return; }
    commit({ ...graph, edges: addEdge({ ...p, markerEnd: arrow(kindOf(tgt?.data.kind).color) }, edges) });
  }, [graph, nodes, edges, commit]);

  const undo = () => { if (!past.length) return; setFuture((f) => [graph, ...f]); setGraph(past[past.length - 1]); setPast((p) => p.slice(0, -1)); };
  const redo = () => { if (!future.length) return; setPast((p) => [...p, graph]); setGraph(future[0]); setFuture((f) => f.slice(1)); };

  useEffect(() => {
    const h = (e) => {
      if (!(e.metaKey || e.ctrlKey) || ["INPUT", "TEXTAREA"].includes(e.target.tagName)) return;
      if (e.key.toLowerCase() === "z") { e.preventDefault(); e.shiftKey ? redo() : undo(); }
      if (e.key.toLowerCase() === "y") { e.preventDefault(); redo(); }
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [graph, past, future]); // eslint-disable-line react-hooks/exhaustive-deps

  const onDrop = (ev) => {
    ev.preventDefault();
    const kind = ev.dataTransfer.getData("application/noetaris-kind");
    if (!kind || !rf.current) return;
    const pos = rf.current.screenToFlowPosition({ x: ev.clientX, y: ev.clientY });
    const id = "n" + Date.now().toString(36);
    commit({ ...graph, nodes: [...nodes, mk(id, pos.x - 100, pos.y - 30, kindOf(kind).label, kind, "draft")] });
    setSelectedId(id);
  };

  const selected = nodes.find((n) => n.id === selectedId);
  const patchSelected = (patch) => ({ ...graph, nodes: nodes.map((n) => (n.id === selectedId ? { ...n, data: { ...n.data, ...patch } } : n)) });
  const updateSelected = (patch) => commit(patchSelected(patch));
  const beginLabelEdit = () => { setPast((p) => [...p.slice(-49), graph]); setFuture([]); };
  const typeLabel = (label) => { setGraph(patchSelected({ label })); setDirty(true); };
  const deleteSelected = () => {
    commit({ nodes: nodes.filter((n) => n.id !== selectedId), edges: edges.filter((e) => e.source !== selectedId && e.target !== selectedId) });
    setSelectedId(null);
  };

  const saveDraft = () => { localStorage.setItem(DRAFT_KEY, JSON.stringify(graph)); setDirty(false); setHasSaved(true); toast.success("Draft saved locally (browser only — backend PUT /v1/workflows/{id}/drafts is CONTRACT_READY)"); };
  const runValidate = () => { const r = validate(nodes, edges); setIssues(r); r.length ? toast.warning(`${r.length} validation issue(s)`) : toast.success("Graph valid — execution requires backend (BLOCKED_BACKEND)"); };
  const resetGraph = () => { setPast((p) => [...p, graph]); setGraph(blank); localStorage.removeItem(DRAFT_KEY); setHasSaved(false); setDirty(false); setIssues(null); };

  const suggest = () => {
    const last = nodes.find((n) => n.data.kind === "output") || nodes[nodes.length - 1];
    const agent = nodes.find((n) => n.data.kind === "agent");
    const upstream = agent || nodes.find((n) => n.data.kind !== "output") || nodes[0];
    const pid = "p" + Date.now().toString(36);
    setProposal({
      summary: "Add a human review gate before publishing and tighten the agent label.",
      add: [{ ...mk(pid, (last?.position.x || 900) - 140, (last?.position.y || 160) + 180, "Human review gate", "govern", "draft"), data: { label: "Human review gate", kind: "govern", status: "draft", diff: "add" } }],
      addEdges: [upstream && ed("pi" + pid, upstream.id, pid, "#F24F61"), last && last.id !== upstream?.id && ed("pe" + pid, pid, last.id, "#48C7A1")].filter(Boolean),
      edit: agent ? [{ id: agent.id, from: agent.data.label, to: agent.data.label + " (cited only)" }] : [],
    });
  };
  const acceptProposal = () => {
    const edited = nodes.map((n) => { const e = proposal.edit.find((x) => x.id === n.id); return e ? { ...n, data: { ...n.data, label: e.to } } : n; });
    commit({ nodes: [...edited, ...proposal.add.map((n) => ({ ...n, data: { ...n.data, diff: undefined } }))], edges: [...edges, ...proposal.addEdges] });
    setProposal(null);
    toast.success("Proposal accepted into local draft");
  };

  const shownNodes = proposal
    ? [...nodes.map((n) => (proposal.edit.some((e) => e.id === n.id) ? { ...n, data: { ...n.data, diff: "edit" } } : n)), ...proposal.add]
    : nodes;
  const shownEdges = proposal ? [...edges, ...proposal.addEdges.map((e) => ({ ...e, style: { strokeDasharray: "6 4", stroke: "#48C7A1" } }))] : edges;

  return (
    <div className="flex h-[calc(100vh-64px)]" data-testid="workflow-studio">
      <aside className="w-60 shrink-0 border-r border-[color:var(--n-stroke-soft)] p-4 overflow-y-auto hidden md:block">
        <div className="text-[10px] uppercase tracking-[0.25em] text-[color:var(--n-text-subtle)] mb-3">Node palette · drag to canvas</div>
        <div className="space-y-2">
          {palette.map((p) => (
            <div key={p.kind} draggable onDragStart={(e) => { e.dataTransfer.setData("application/noetaris-kind", p.kind); e.dataTransfer.effectAllowed = "move"; }}
              className="n-glass rounded-lg p-3 flex items-center gap-3 cursor-grab active:cursor-grabbing hover:border-[rgba(46,155,255,0.4)] transition-colors"
              data-testid={`palette-${p.kind}`}>
              <div className="w-8 h-8 rounded-md flex items-center justify-center" style={{ background: p.color + "22", border: `1px solid ${p.color}66` }}>
                <p.icon size={14} color={p.color} />
              </div>
              <div>
                <div className="text-sm">{p.label}</div>
                <div className="text-[10px] uppercase tracking-widest" style={{ color: p.color }}>{p.kind}</div>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-6 text-[10px] uppercase tracking-widest text-[color:var(--n-text-subtle)]">AI proposal · DEMO_FIXTURE</div>
        <button onClick={suggest} disabled={!!proposal} className="n-cta w-full h-10 rounded-xl text-xs mt-2 flex items-center justify-center gap-2 disabled:opacity-50" data-testid="studio-suggest-btn">
          <Sparkles size={12} /> Suggest changes
        </button>
        <div className="mt-2 n-glass rounded-lg p-2 text-[11px] text-[color:var(--n-text-mute)]">Proposals arrive as a diff. Nothing changes until you accept.</div>
        <button onClick={resetGraph} className="n-btn-ghost w-full h-9 text-xs mt-4" data-testid="studio-reset-btn">{id === "new" ? "Clear canvas" : "Reset to sample"}</button>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <div className="flex items-center gap-2 h-14 border-b border-[color:var(--n-stroke-soft)] px-5">
          <h2 className="font-display text-lg truncate">{id === "new" ? "New workflow (draft)" : `${id} · revision 37 (draft)`}</h2>
          <span className={"n-chip " + (dirty ? "n-chip-amber" : hasSaved ? "n-chip-green" : "")} data-testid="studio-dirty-badge">{dirty ? "UNSAVED" : hasSaved ? "SAVED LOCALLY" : "NOT SAVED"}</span>
          <span className="text-[11px] text-[color:var(--n-text-subtle)] font-mono hidden lg:inline">{nodes.length} nodes · {edges.length} edges</span>
          <div className="ml-auto flex items-center gap-2">
            <button onClick={undo} disabled={!past.length} className="n-btn-ghost w-9 h-9 flex items-center justify-center disabled:opacity-40" aria-label="Undo" data-testid="studio-undo-btn"><Undo2 size={14} /></button>
            <button onClick={redo} disabled={!future.length} className="n-btn-ghost w-9 h-9 flex items-center justify-center disabled:opacity-40" aria-label="Redo" data-testid="studio-redo-btn"><Redo2 size={14} /></button>
            <button onClick={saveDraft} className="n-btn-ghost px-3 h-9 flex items-center gap-2 text-xs" data-testid="studio-save-btn"><Save size={12} />Save draft</button>
            <button onClick={runValidate} className="n-cta px-4 h-9 flex items-center gap-2 text-xs" data-testid="studio-validate-btn"><Play size={12} />Validate</button>
          </div>
        </div>

        <div className="flex-1 relative" onDrop={onDrop} onDragOver={(e) => e.preventDefault()} data-testid="studio-canvas">
          <ReactFlow nodes={shownNodes} edges={shownEdges} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange} onConnect={onConnect}
            onInit={(i) => (rf.current = i)} onNodeClick={(_, n) => setSelectedId(n.id)} onPaneClick={() => setSelectedId(null)}
            nodeTypes={nodeTypes} fitView deleteKeyCode={["Backspace", "Delete"]} multiSelectionKeyCode="Shift" proOptions={{ hideAttribution: true }}>
            <Background color="rgba(255,255,255,0.05)" gap={28} />
            <MiniMap pannable zoomable nodeColor={(n) => kindOf(n.data?.kind).color} maskColor="rgba(5,10,19,0.7)" style={{ background: "#0A1321" }} />
            <Controls showInteractive={false} />
          </ReactFlow>

          {proposal && (
            <div className="absolute top-4 left-1/2 -translate-x-1/2 n-glass rounded-2xl p-4 w-[460px] z-10" data-testid="studio-proposal-panel">
              <div className="flex items-center gap-2 mb-2"><Sparkles size={14} className="text-[color:var(--n-cyan)]" /><span className="text-sm">AI proposal — review diff</span><span className="n-chip n-chip-amber ml-auto">DEMO_FIXTURE</span></div>
              <div className="text-xs text-[color:var(--n-text-mute)] mb-3">{proposal.summary}</div>
              <ul className="text-xs space-y-1 mb-3 font-mono">
                {proposal.add.map((n) => <li key={n.id} className="text-[color:var(--n-green)]">+ node “{n.data.label}” ({n.data.kind})</li>)}
                {proposal.addEdges.map((e) => <li key={e.id} className="text-[color:var(--n-green)]">+ edge {e.source} → {e.target}</li>)}
                {proposal.edit.map((e) => <li key={e.id} className="text-[color:var(--n-amber)]">~ {e.id}: “{e.from}” → “{e.to}”</li>)}
              </ul>
              <div className="flex gap-2">
                <button onClick={acceptProposal} className="n-cta h-9 px-4 text-xs flex items-center gap-1" data-testid="studio-accept-proposal"><Check size={12} />Accept</button>
                <button onClick={() => setProposal(null)} className="n-btn-ghost h-9 px-4 text-xs flex items-center gap-1" data-testid="studio-reject-proposal"><X size={12} />Reject</button>
              </div>
            </div>
          )}
        </div>

        <div className="h-36 border-t border-[color:var(--n-stroke-soft)] p-3 flex gap-3 overflow-x-auto" data-testid="studio-dock">
          {issues === null ? (
            <div className="text-xs text-[color:var(--n-text-subtle)] self-center px-3">Validation dock — press <b>Validate</b> to check port connections and governance coverage. Live traces appear here only when the backend streams execution events.</div>
          ) : issues.length === 0 ? (
            <div className="n-glass rounded-xl p-3 flex items-center gap-2 text-sm"><CheckCircle2 size={16} className="text-[color:var(--n-green)]" /> All {nodes.length} nodes connected · governance present</div>
          ) : issues.map((t) => (
            <div key={t} className="n-glass rounded-xl p-3 min-w-[240px]">
              <div className="flex items-center gap-1 text-[10px] uppercase tracking-widest text-[color:var(--n-amber)]"><AlertTriangle size={11} />Validation</div>
              <div className="text-xs mt-2">{t}</div>
            </div>
          ))}
        </div>
      </div>

      <aside className="w-80 shrink-0 border-l border-[color:var(--n-stroke-soft)] p-5 overflow-y-auto hidden lg:block" data-testid="workflow-inspector">
        <div className="flex items-center gap-2 mb-3">
          <Settings size={14} className="text-[color:var(--n-text-subtle)]" />
          <div className="text-[10px] uppercase tracking-[0.25em] text-[color:var(--n-text-subtle)]">Inspector</div>
        </div>
        {selected ? (
          <>
            <div className="text-[10px] uppercase tracking-widest mb-1" style={{ color: kindOf(selected.data.kind).color }}>{selected.data.kind} · {selected.id}</div>
            <label className="block mb-3">
              <span className="text-[10px] uppercase tracking-widest text-[color:var(--n-text-subtle)]">Label</span>
              <input value={selected.data.label} onFocus={beginLabelEdit} onChange={(e) => typeLabel(e.target.value)}
                className="mt-1 w-full h-9 px-3 rounded-lg n-glass text-sm outline-none" data-testid="inspector-label-input" />
            </label>
            <label className="block mb-3">
              <span className="text-[10px] uppercase tracking-widest text-[color:var(--n-text-subtle)]">Status</span>
              <select value={selected.data.status} onChange={(e) => updateSelected({ status: e.target.value })}
                className="mt-1 w-full h-9 px-2 rounded-lg n-glass text-sm outline-none bg-[color:var(--n-bg-elev)]" data-testid="inspector-status-select">
                {["draft", "ready", "active", "restricted"].map((s) => <option key={s}>{s}</option>)}
              </select>
            </label>
            {[{ k: "Model", v: "GPT-5 reserved" }, { k: "Timeout", v: "120s" }, { k: "Retry policy", v: "exp backoff · 3 attempts" }, { k: "Scope", v: "source: current revision" }, { k: "Permissions", v: "governed-run" }].map((f) => (
              <div key={f.k} className="mb-3">
                <div className="text-[10px] uppercase tracking-widest text-[color:var(--n-text-subtle)]">{f.k}</div>
                <div className="text-sm">{f.v}</div>
              </div>
            ))}
            <div className="text-[11px] text-[color:var(--n-text-subtle)] mb-3">Only backend-registered node types may execute. This node is a visual draft until registered.</div>
            <button onClick={deleteSelected} className="n-btn-ghost w-full h-10 rounded-xl text-xs flex items-center justify-center gap-2 hover:!border-[rgba(242,79,97,0.5)]" data-testid="inspector-delete-btn"><Trash2 size={12} />Delete node</button>
          </>
        ) : (
          <div className="text-sm text-[color:var(--n-text-subtle)]">Select a node to inspect. Shift-click to multi-select, Delete to remove, ⌘Z / ⌘⇧Z to undo/redo.</div>
        )}
      </aside>
    </div>
  );
}
