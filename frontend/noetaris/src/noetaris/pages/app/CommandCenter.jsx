import React, { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { 
  ArrowUpRight, AlertTriangle, Cpu, Database, FileText, GitMerge, RefreshCw
} from "lucide-react";
import { apiRequest } from "../../services/api";

const emptyTelemetry = {
  loading: true,
  documents: null,
  claims: null,
  capabilities: null,
  model: null,
  errors: {},
};

export default function CommandCenter() {
  const [telemetry, setTelemetry] = useState(emptyTelemetry);
  const [refreshing, setRefreshing] = useState(false);
  const requestVersion = useRef(0);
  const activeRequest = useRef(null);

  const fetchLiveTelemetry = async () => {
    activeRequest.current?.abort();
    const controller = new AbortController();
    activeRequest.current = controller;
    const version = ++requestVersion.current;
    setRefreshing(true);
    setTelemetry({ ...emptyTelemetry, loading: true });
    const results = await Promise.allSettled([
      apiRequest('/v1/documents?limit=5', { signal: controller.signal }),
      apiRequest('/v1/claims?limit=10', { signal: controller.signal }),
      apiRequest('/v1/capabilities', { signal: controller.signal }),
      apiRequest('/v1/model/status', { signal: controller.signal }),
    ]);
    if (version !== requestVersion.current) return;

    const [documentsResult, claimsResult, capabilitiesResult, modelResult] = results;
    const documents = documentsResult.status === 'fulfilled' &&
      Number.isSafeInteger(documentsResult.value?.total) &&
      documentsResult.value.total >= 0 &&
      Array.isArray(documentsResult.value.items)
      ? documentsResult.value : null;
    const claims = claimsResult.status === 'fulfilled' &&
      Number.isSafeInteger(claimsResult.value?.total) &&
      claimsResult.value.total >= 0 &&
      Array.isArray(claimsResult.value.items)
      ? claimsResult.value : null;
    const capabilities = capabilitiesResult.status === 'fulfilled' &&
      capabilitiesResult.value && typeof capabilitiesResult.value === 'object'
      ? capabilitiesResult.value : null;
    const model = modelResult.status === 'fulfilled' &&
      typeof modelResult.value?.configured === 'boolean' &&
      typeof modelResult.value?.reachable === 'boolean' &&
      typeof modelResult.value?.model_loaded === 'boolean'
      ? modelResult.value : null;

    setTelemetry({
      loading: false,
      documents,
      claims,
      capabilities,
      model,
      errors: {
        documents: documents ? null : 'Document data is unavailable or invalid.',
        claims: claims ? null : 'Claim data is unavailable or invalid.',
        capabilities: capabilities ? null : 'Capabilities are unavailable or invalid.',
        model: model ? null : 'Model status is unavailable or invalid.',
      },
    });
    setRefreshing(false);
  };

  useEffect(() => {
    fetchLiveTelemetry();
    return () => {
      requestVersion.current++;
      activeRequest.current?.abort();
    };
  }, []);

  const kpis = [
    { label: "Authorized Documents", value: telemetry.documents?.total, error: telemetry.errors.documents, sub: "Current document API result" },
    { label: "Retained Claims", value: telemetry.claims?.total, error: telemetry.errors.claims, sub: "Current claim API result" },
    {
      label: "Unresolved Conflicts",
      value: telemetry.claims?.summary?.conflict_analysis_complete === true && Array.isArray(telemetry.claims.conflicts)
        ? telemetry.claims.conflicts.length : null,
      error: telemetry.errors.claims || (telemetry.claims?.summary?.conflict_analysis_complete === true
        && Array.isArray(telemetry.claims?.conflicts) ? null : "Conflict analysis is incomplete or unavailable."),
      sub: "Only complete conflict analysis is counted",
    },
    {
      label: "Inference Model",
      value: telemetry.model?.model_loaded ? "Loaded" : telemetry.model?.reachable ? "Not loaded" : null,
      error: telemetry.errors.model,
      sub: telemetry.model?.model
        ? `${telemetry.model.provider || "Provider unavailable"} · ${telemetry.model.model} · E2E qualification not implied`
        : "Model identity unavailable",
    },
  ];

  return (
    <div className="p-4 md:p-8 relative" data-testid="command-center">
      {/* Hero header */}
      <div className="n-glass rounded-2xl p-5 md:p-7 mb-6 overflow-hidden relative border border-[color:var(--n-stroke-soft)]">
        <div 
          className="absolute inset-0 pointer-events-none" 
          style={{
            background: "radial-gradient(600px 300px at 85% 50%, rgba(46,155,255,0.18), transparent 70%)"
          }} 
        />
        <div className="relative z-10 flex flex-col md:flex-row items-start justify-between gap-6">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-[11px] uppercase tracking-[0.3em] text-[color:var(--n-cyan)] font-mono">
                Command Center
              </span>
              <span className="n-chip n-chip text-[10px] py-0.5">
                {telemetry.loading ? "LIVE CHECKS PENDING" : "LIVE CHECKS RETURNED"}
              </span>
            </div>
            <h1 className="font-display text-3xl md:text-4xl mb-2 text-white">
              Noetaris Operations
            </h1>
            <p className="text-[color:var(--n-text-mute)] max-w-2xl text-sm leading-relaxed">
              Current observations from authorized document, claim, capability, and model APIs. Detailed
              parser, database, agent, and workflow health is not reported by this dashboard.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link to="/app/chat" className="n-cta px-5 h-10 flex items-center gap-2 text-xs font-semibold">
                Ask AI Assistant <ArrowUpRight size={14}/>
              </Link>
              <Link to="/app/library" className="n-btn-ghost px-5 h-10 flex items-center gap-2 text-xs">
                <FileText size={14} /> Upload Manual
              </Link>
              <Link to="/app/knowledge/review" className="n-btn-ghost px-5 h-10 flex items-center gap-2 text-xs text-amber-300 hover:text-amber-200">
                <AlertTriangle size={14} /> Review Conflicts ({kpis[2].value ?? "unavailable"})
              </Link>
              <button 
                onClick={fetchLiveTelemetry} 
                disabled={refreshing}
                className="n-btn-ghost px-3 h-10 flex items-center gap-1.5 text-xs text-slate-400 hover:text-white"
                title="Refresh Live Telemetry"
              >
                <RefreshCw size={13} className={refreshing ? "animate-spin" : ""} />
              </button>
            </div>
          </div>
          <TopologyMotif />
        </div>
      </div>

      {/* Real Live KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {kpis.map((k) => (
          <div key={k.label} className="n-panel rounded-xl p-5 border border-[color:var(--n-stroke-soft)]" data-testid={`kpi-${k.label.toLowerCase().replace(/[^a-z]/g,'')}`}>
            <div className="text-xs text-[color:var(--n-text-subtle)] mb-1 font-medium">{k.label}</div>
            <div className="flex items-end justify-between">
              <div className="font-display text-2xl text-white">
                {k.value ?? (telemetry.loading ? "Loading…" : "Unavailable")}
              </div>
            </div>
            <div className="text-[10px] text-slate-500 font-mono mt-2">{k.error || k.sub}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Admitted Source Documents */}
        <div className="n-glass rounded-2xl p-5 lg:col-span-1 border border-[color:var(--n-stroke-soft)]">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-display text-base text-white flex items-center gap-2">
              <Database size={16} className="text-[color:var(--n-cyan)]" />
              Source Documents
            </h3>
            <Link to="/app/library" className="text-xs text-[color:var(--n-cyan)] hover:underline">
              Library →
            </Link>
          </div>
          {telemetry.errors.documents && !telemetry.loading && <p role="status" className="text-xs text-amber-300">{telemetry.errors.documents}</p>}
          <ul className="space-y-2">
            {(telemetry.documents?.items || []).filter(doc => typeof doc?.id === "string").map((doc) => (
              <li key={doc.id} className="p-2.5 rounded-xl bg-black/20 hover:bg-white/5 border border-white/5 transition-colors">
                <Link to={`/app/documents/${doc.id}`} className="block">
                  <div className="text-xs font-semibold text-white truncate">{doc.title || "Untitled source"}</div>
                  <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono mt-1">
                    <span>Rev {doc.version || "unavailable"}</span>
                    <span className="text-[color:var(--n-blue)] truncate max-w-[120px]">{doc.sha256?.slice(0, 12)}…</span>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
          {!telemetry.loading && !telemetry.errors.documents && telemetry.documents.items.length === 0 &&
            <p role="status" className="text-xs text-slate-400">No documents are present in this authorized result.</p>}
        </div>

        {/* Conflicting Knowledge Items */}
        <div className="n-glass rounded-2xl p-5 lg:col-span-1 border border-[color:var(--n-stroke-soft)]">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-display text-base text-white flex items-center gap-2">
              <GitMerge size={16} className="text-amber-400" />
              Governed Conflicts
            </h3>
            <Link to="/app/knowledge/review" className="text-xs text-amber-400 hover:underline">
              Review Queue →
            </Link>
          </div>
          {telemetry.claims?.summary?.conflict_analysis_complete !== true || !Array.isArray(telemetry.claims?.conflicts) ? (
            <p role="status" className="text-xs text-amber-300">
              Conflict analysis is incomplete or unavailable; absence of conflicts is not established.
            </p>
          ) : telemetry.claims.conflicts.length > 0 ? (
            <div className="space-y-3">
              {telemetry.claims.conflicts.map((conf, idx) => (
                <div key={idx} className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs">
                  <div className="font-bold text-amber-300">{conf.subject}</div>
                  <div className="text-[11px] text-slate-300 mt-0.5">{conf.predicate}</div>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {Object.keys(conf.alternatives || {}).map((alt) => (
                      <span key={alt} className="px-2 py-0.5 rounded bg-black/40 text-[10px] font-mono text-amber-200 border border-amber-500/30">
                        {alt}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
              <div className="text-[11px] text-slate-400 p-1">
                Discrepancies between supplier specs are isolated to prevent automated hallucination.
              </div>
            </div>
          ) : (
            <div className="p-6 text-center text-xs text-slate-400">
              No unresolved conflicts were returned by the complete current analysis.
            </div>
          )}
        </div>

        {/* Engine & Runtime Topology */}
        <div className="n-glass rounded-2xl p-5 lg:col-span-1 border border-[color:var(--n-stroke-soft)]">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-display text-base text-white flex items-center gap-2">
              <Cpu size={16} className="text-[color:var(--n-blue)]" />
              Observed Services
            </h3>
            <Link to="/app/integrations" className="text-xs text-[color:var(--n-blue)] hover:underline">
              Inspect →
            </Link>
          </div>
          <ul className="space-y-2.5 text-xs">
            {[
              { name: "Document API", available: !!telemetry.documents },
              { name: "Claim API", available: !!telemetry.claims },
              {
                name: "Model inventory API",
                available: !!telemetry.model?.reachable,
                detail: telemetry.model?.model || "Model identity unavailable",
              },
              {
                name: "Content access",
                available: telemetry.capabilities?.content_access?.admitted === true,
                status: typeof telemetry.capabilities?.content_access?.admitted === "boolean"
                  ? telemetry.capabilities.content_access.admitted ? "Admitted" : "Not admitted"
                  : "Unavailable",
                detail: telemetry.capabilities?.content_access?.reason || "Current identity capability",
              },
              { name: "Parser / database health", detail: "Not reported by the dashboard API" },
            ].map(svc => (
              <li key={svc.name} className="flex items-center justify-between gap-3 p-2 rounded-lg bg-black/20 border border-white/5">
                <div>
                  <div className="text-white font-medium text-xs">{svc.name}</div>
                  {svc.detail && <div className="text-[10px] text-slate-500 font-mono">{svc.detail}</div>}
                </div>
                <span className={`n-chip text-[9px] py-0.5 ${svc.available ? "n-chip-green" : "n-chip-amber"}`}>
                  {telemetry.loading ? "Checking" : svc.status || (svc.available ? "Responded" : "Unavailable")}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

function TopologyMotif() {
  return (
    <div className="w-48 h-32 relative shrink-0 hidden md:block">
      <svg viewBox="0 0 190 120" className="w-full h-full opacity-70">
        <defs>
          <linearGradient id="edge-blue" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#2E9BFF" stopOpacity="0.8"/>
            <stop offset="100%" stopColor="#C41E2A" stopOpacity="0.8"/>
          </linearGradient>
        </defs>
        <line x1="30" y1="60" x2="95" y2="25" stroke="url(#edge-blue)" strokeWidth="1.5" strokeDasharray="3 3"/>
        <line x1="95" y1="25" x2="160" y2="60" stroke="url(#edge-blue)" strokeWidth="1.5"/>
        <line x1="30" y1="60" x2="95" y2="95" stroke="url(#edge-blue)" strokeWidth="1.5"/>
        <line x1="95" y1="95" x2="160" y2="60" stroke="url(#edge-blue)" strokeWidth="1.5" strokeDasharray="3 3"/>
        <line x1="95" y1="25" x2="95" y2="95" stroke="rgba(46,155,255,0.4)" strokeWidth="1"/>

        <circle cx="30" cy="60" r="8" fill="#0A1321" stroke="#2E9BFF" strokeWidth="2"/>
        <circle cx="95" cy="25" r="9" fill="#0A1321" stroke="#2E9BFF" strokeWidth="2"/>
        <circle cx="95" cy="95" r="9" fill="#0A1321" stroke="#C41E2A" strokeWidth="2"/>
        <circle cx="160" cy="60" r="10" fill="#0A1321" stroke="#5ED6ED" strokeWidth="2"/>
      </svg>
    </div>
  );
}
