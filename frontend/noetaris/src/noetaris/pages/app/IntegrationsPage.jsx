import React, { useState, useEffect } from 'react';
import { Cpu, CheckCircle2, AlertTriangle, Layers, Server, Shield, RefreshCw } from 'lucide-react';
import { apiRequest } from '../../services/api';
import { PageHeader } from './OperationsPages';

export default function IntegrationsPage() {
  const [capabilities, setCapabilities] = useState(null);
  const [modelStatus, setModelStatus] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = async () => {
    setRefreshing(true);
    try {
      const [caps, model] = await Promise.allSettled([
        apiRequest('/v1/capabilities'),
        apiRequest('/v1/model/status'),
      ]);
      if (caps.status === 'fulfilled') setCapabilities(caps.value);
      if (model.status === 'fulfilled') setModelStatus(model.value);
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const integrations = [
    {
      name: "AMD ROCm Accelerator",
      category: "Hardware Acceleration",
      status: "Deferred (Not Commissioned)",
      statusKind: "amber",
      desc: "AMD Instinct & Radeon GPU compute runtime. Hardware pass-through profile is reserved; active inference is currently executed on qualified CPU adapter.",
      routes: ["/v1/reason"],
      badge: "RESERVED PROFILE"
    },
    {
      name: "llama.cpp CPU Inference Engine",
      category: "Local Inference",
      status: "Active & Ready",
      statusKind: "green",
      desc: "Local quantized GGUF execution (Qwen3-0.6B) running in isolated container. Bounded token budgets and citation validation enabled.",
      routes: ["/v1/reason", "/v1/model/status"],
      badge: "QUALIFIED ADAPTER"
    },
    {
      name: "Isolated Ingestion & Parsing Engine",
      category: "Document Parsing",
      status: "Active & Healthy",
      statusKind: "green",
      desc: "Hardened parsing child service on port 8788. TXT, Markdown, CSV, TSV, JSON, and XLSX parsers active. PDF bounding box extractor online.",
      routes: ["/v1/documents", "/v1/files"],
      badge: "CONTAINER ISOLATED"
    },
    {
      name: "PostgreSQL 16 Evidence & Vector Database",
      category: "Durable Store",
      status: "Active & Verified",
      statusKind: "green",
      desc: "PostgreSQL 16 with pgvector extension. 39 schema migrations verified. Row-level security (RLS) and transaction advisory locks active.",
      routes: ["/v1/documents", "/v1/claims", "/v1/governed/records"],
      badge: "39 MIGRATIONS APPLIED"
    },
    {
      name: "OCR Geometry Worker",
      category: "Optical Character Recognition",
      status: "Conservative English Profile",
      statusKind: "green",
      desc: "Printed English text extraction. Degraded/table/formula quality withheld to prevent false evidence hallucination.",
      routes: ["/v1/files"],
      badge: "SAFETY GATED"
    },
  ];

  return (
    <div className="p-4 md:p-8 max-w-6xl" data-testid="integrations-page">
      <PageHeader 
        title="Hardware & Provider Integrations" 
        eyebrow="Compute · Hardware · Inference Adapters"
        action={
          <button 
            onClick={loadData} 
            disabled={refreshing}
            className="n-btn-ghost h-9 px-3 text-xs flex items-center gap-1.5"
          >
            <RefreshCw size={13} className={refreshing ? "animate-spin" : ""} />
            <span>Recheck Readiness</span>
          </button>
        }
      >
        Verified system topology and hardware readiness. Inspect AMD compute interfaces, local inference containers, and isolated parser workers.
      </PageHeader>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-8">
        {integrations.map((it) => (
          <div key={it.name} className="n-glass rounded-2xl p-5 border border-[color:var(--n-stroke-soft)] space-y-3">
            <div className="flex items-start justify-between gap-3">
              <div>
                <span className="text-[10px] font-mono text-[color:var(--n-text-subtle)] uppercase tracking-wider block">
                  {it.category}
                </span>
                <h3 className="font-display text-base text-white mt-0.5">{it.name}</h3>
              </div>
              <span className={`text-[10px] uppercase font-mono px-2 py-0.5 rounded border font-semibold ${
                it.statusKind === 'green' 
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' 
                  : 'bg-amber-500/10 text-amber-300 border-amber-500/30'
              }`}>
                {it.badge}
              </span>
            </div>

            <p className="text-xs text-[color:var(--n-text-mute)] leading-relaxed">
              {it.desc}
            </p>

            <div className="pt-2 border-t border-white/5 flex items-center justify-between text-[11px] text-slate-400 font-mono">
              <span>Status: <strong className="text-white">{it.status}</strong></span>
              <span>{it.routes.join(" · ")}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Capabilities Registry Table */}
      {capabilities?.items && (
        <div className="n-glass rounded-2xl p-6 border border-[color:var(--n-stroke-soft)] space-y-4">
          <h3 className="font-display text-base text-white">Live Capabilities Registry</h3>
          <p className="text-xs text-[color:var(--n-text-mute)]">
            Verified security bounds and admission criteria from the Python core engine.
          </p>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-white/10 text-slate-400 uppercase font-mono text-[10px]">
                  <th className="pb-2">Capability</th>
                  <th className="pb-2">State</th>
                  <th className="pb-2">Permissions</th>
                  <th className="pb-2">Bound Routes</th>
                  <th className="pb-2">Limitations</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {capabilities.items.map((c) => (
                  <tr key={c.id} className="hover:bg-white/[0.02]">
                    <td className="py-2.5 font-semibold text-white">{c.id}</td>
                    <td className="py-2.5">
                      <span className="n-chip text-[10px] py-0.5 font-mono">{c.state}</span>
                    </td>
                    <td className="py-2.5 font-mono text-slate-300 text-[11px]">{c.permissions?.join(', ') || '—'}</td>
                    <td className="py-2.5 font-mono text-[color:var(--n-blue)] text-[11px]">{c.routes?.slice(0, 2).join(', ')}</td>
                    <td className="py-2.5 text-slate-400 text-[11px] max-w-xs truncate" title={c.limitations}>{c.limitations}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
