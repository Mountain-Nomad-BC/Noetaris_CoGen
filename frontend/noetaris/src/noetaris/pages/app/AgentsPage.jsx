import React, { useState } from 'react';
import { Bot, Sparkles, CheckCircle2, AlertTriangle, Shield, Play, Settings, Plus } from 'lucide-react';
import { PageHeader } from './OperationsPages';
import { toast } from 'sonner';

const AGENTS = [
  {
    id: "agent-parser",
    name: "Document Ingestion & Geometry Parser",
    role: "Parser Worker",
    status: "Active",
    endpoint: "http://parser:8788",
    routes: ["/v1/documents", "/v1/files"],
    util: 42,
    tasksCompleted: 148,
    desc: "Isolated child worker parsing PDF layout trees, bounding box coordinates, and tabular cell grids.",
  },
  {
    id: "agent-indexer",
    name: "Semantic Indexing & Vectorization Agent",
    role: "Index Worker",
    status: "Active",
    endpoint: "internal:worker_loop",
    routes: ["/v1/sources/{id}/index", "/v1/knowledge/semantic-search"],
    util: 68,
    tasksCompleted: 512,
    desc: "Durable SQLite/PostgreSQL queue processor generating 384-dimensional exact cosine embeddings.",
  },
  {
    id: "agent-grounder",
    name: "Source Grounding & Citation Anchor",
    role: "Evidence Agent",
    status: "Active",
    endpoint: "internal:retrieval_query",
    routes: ["/v1/search", "/v1/chat"],
    util: 84,
    tasksCompleted: 980,
    desc: "Extracts immutable text spans, cross-references supplier revisions, and anchors geometry for PDF highlighting.",
  },
  {
    id: "agent-reasoner",
    name: "Local CPU Bounded Reasoner",
    role: "Inference Engine",
    status: "Active",
    endpoint: "http://llama-cpp:8080",
    routes: ["/v1/reason"],
    util: 55,
    tasksCompleted: 240,
    desc: "Executes Qwen3-0.6B with hard token caps and conservative support guards to prevent hallucinated numbers.",
  },
  {
    id: "agent-quarantine",
    name: "Conflict Resolution & Quarantine Sentry",
    role: "Safety Sentry",
    status: "Active",
    endpoint: "internal:conflict_groups",
    routes: ["/v1/claims", "/v1/review/{id}"],
    util: 15,
    tasksCompleted: 88,
    desc: "Monitors disparate supplier claims (e.g. Pump-X 75C vs 85C) and isolates contradictions from automated promotion.",
  },
  {
    id: "agent-governor",
    name: "Audit Trail & Governed Ledger",
    role: "Governance Auditor",
    status: "Active",
    endpoint: "internal:governed_store",
    routes: ["/v1/governed/records", "/v1/admin/actions"],
    util: 28,
    tasksCompleted: 432,
    desc: "Enforces two-man rule on policy modifications, tracks immutable SHA-256 seals, and records audit events.",
  },
];

export default function AgentsPage() {
  const [agents, setAgents] = useState(AGENTS);

  const handleTestAgent = (agentName) => {
    toast.success(`Dispatched health verification ping to ${agentName}`);
  };

  return (
    <div className="p-4 md:p-8 max-w-6xl" data-testid="agents-page">
      <PageHeader 
        title="Agent Fleet & Worker Orchestration" 
        eyebrow="Multi-Agent Systems · Worker Pools · Bounded Roles"
        action={
          <button 
            onClick={() => toast.info('New agent role provisioning template opened')}
            className="n-cta h-9 px-4 text-xs flex items-center gap-1.5"
          >
            <Plus size={14} />
            <span>Deploy Agent Role</span>
          </button>
        }
      >
        Specialized autonomous agents executing distinct stages of the engineering intelligence pipeline with strict permission boundaries.
      </PageHeader>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {agents.map((ag) => (
          <div key={ag.id} className="n-glass rounded-2xl p-5 border border-[color:var(--n-stroke-soft)] flex flex-col justify-between space-y-4">
            <div className="space-y-3">
              <div className="flex items-start justify-between">
                <div className="w-9 h-9 rounded-xl bg-[color:var(--n-blue)]/10 border border-[color:var(--n-blue)]/30 flex items-center justify-center text-[color:var(--n-blue)]">
                  <Bot size={18} />
                </div>
                <span className="n-chip-green n-chip text-[10px] py-0.5">
                  ● {ag.status.toUpperCase()}
                </span>
              </div>

              <div>
                <h3 className="font-display text-base text-white">{ag.name}</h3>
                <span className="text-[10px] font-mono uppercase tracking-wider text-[color:var(--n-cyan)] block mt-0.5">
                  {ag.role}
                </span>
              </div>

              <p className="text-xs text-[color:var(--n-text-mute)] leading-relaxed">
                {ag.desc}
              </p>

              <div className="pt-2 space-y-1.5 text-[11px] font-mono text-slate-400">
                <div className="flex justify-between">
                  <span>Capacity Utilization:</span>
                  <span className="text-white font-semibold">{ag.util}%</span>
                </div>
                <div className="w-full h-1.5 rounded-full bg-white/5 overflow-hidden">
                  <div className="h-full rounded-full bg-gradient-to-r from-[#1A6BB5] to-[#2E9BFF]" style={{ width: `${ag.util}%` }} />
                </div>
                <div className="flex justify-between pt-1">
                  <span>Completed Tasks:</span>
                  <span className="text-white">{ag.tasksCompleted}</span>
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-white/5 flex items-center justify-between">
              <span className="text-[10px] text-slate-500 font-mono truncate max-w-[150px]">{ag.endpoint}</span>
              <button 
                onClick={() => handleTestAgent(ag.name)}
                className="n-btn-ghost h-7 px-2.5 text-[11px] flex items-center gap-1 hover:text-white"
              >
                <Play size={11} />
                <span>Test Ping</span>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
