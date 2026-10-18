import React, { useState } from "react";
import { Link, useOutletContext } from "react-router-dom";
import { toast } from "sonner";
import { LogViewer } from "./ExecutionsPage";
import * as Icons from "lucide-react";
import { demoCosts, demoAuditLog, demoModels, demoAgents, demoWorkflows } from "../../data/fixtures";
import Sparkline from "../../components/Sparkline";
import { mode } from "../../services/api";
import LiveCostsPage from "./LiveCostsPage";

// A reusable page header
export function PageHeader({ title, eyebrow, action, children }) {
  return (
    <div className="mb-6">
      <div className="text-[11px] uppercase tracking-[0.3em] text-[color:var(--n-cyan)] mb-1">{eyebrow}</div>
      <div className="flex items-end justify-between gap-4">
        <h1 className="font-display text-3xl">{title}</h1>
        <div className="flex items-center gap-2">{action}</div>
      </div>
      {children && <div className="mt-3 text-sm text-[color:var(--n-text-mute)] max-w-3xl">{children}</div>}
      <div className="n-divider mt-5"/>
    </div>
  );
}

export function CostsPage() {
  return mode === "live" ? <LiveCostsPage /> : <DemoCostsPage />;
}

function DemoCostsPage() {
  const pct = Math.round((demoCosts.spend / demoCosts.cap)*100);
  return (
    <div className="p-4 md:p-8" data-testid="costs-page">
      <PageHeader title="Cost & Usage" eyebrow="DEMO_FIXTURE" action={
        <button onClick={()=>{const a=document.createElement("a");a.href=URL.createObjectURL(new Blob([["provider,usd",...demoCosts.byProvider.map(p=>p.label+","+p.value)].join("\n")],{type:"text/csv"}));a.download="noetaris-costs-demo.csv";a.click();}} className="n-btn-ghost h-9 px-4 flex items-center gap-2 text-xs" data-testid="costs-export-btn"><Icons.Download size={12}/> Export CSV</button>
      }>
        Spend by provider over {demoCosts.period}. Provider alerting is not a hard stop — all figures are illustrative.
      </PageHeader>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <div className="n-glass rounded-2xl p-5 lg:col-span-1">
          <div className="text-[11px] uppercase tracking-widest text-[color:var(--n-text-subtle)]">Budget ring</div>
          <div className="font-display text-4xl mt-2">${demoCosts.spend.toLocaleString()}</div>
          <div className="text-sm text-[color:var(--n-text-mute)]">of ${demoCosts.cap.toLocaleString()} cap · {pct}% used</div>
          <div className="mt-5 relative w-44 h-44 mx-auto">
            <svg viewBox="0 0 100 100" className="w-full h-full">
              <circle cx="50" cy="50" r="40" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="10"/>
              <circle cx="50" cy="50" r="40" fill="none" stroke="url(#g1)" strokeWidth="10" strokeLinecap="round"
                strokeDasharray={2*Math.PI*40} strokeDashoffset={(2*Math.PI*40) * (1 - pct/100)} transform="rotate(-90 50 50)"/>
              <defs>
                <linearGradient id="g1" x1="0" x2="1"><stop offset="0" stopColor="#2E9BFF"/><stop offset="1" stopColor="#F24F61"/></linearGradient>
              </defs>
            </svg>
            <div className="absolute inset-0 flex items-center justify-center font-display text-3xl">{pct}%</div>
          </div>
        </div>
        <div className="n-glass rounded-2xl p-5 lg:col-span-2">
          <div className="text-[11px] uppercase tracking-widest text-[color:var(--n-text-subtle)] mb-3">Daily spend</div>
          <Sparkline data={demoCosts.daily.map(d=>d.v)} w={680} h={160} />
          <div className="grid grid-cols-5 gap-3 mt-5">
            {demoCosts.byProvider.map((p)=>(
              <div key={p.label} className="n-panel rounded-lg p-3">
                <div className="text-xs text-[color:var(--n-text-subtle)]">{p.label}</div>
                <div className="font-mono text-lg">${p.value}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="n-glass rounded-2xl p-5">
        <div className="text-[11px] uppercase tracking-widest text-[color:var(--n-text-subtle)] mb-3">Provider line items</div>
        <table className="w-full text-sm min-w-[640px]">
          <thead>
            <tr className="text-[color:var(--n-text-subtle)] text-xs uppercase tracking-widest">
              <th className="text-left py-2 font-normal">Provider</th>
              <th className="text-right font-normal">Share</th>
              <th className="text-right font-normal">Req/min</th>
              <th className="text-right font-normal">Status</th>
            </tr>
          </thead>
          <tbody>
            {demoModels.map((m) => (
              <tr key={m.name} className="border-t border-[color:var(--n-stroke-soft)]">
                <td className="py-2.5 flex items-center gap-3">
                  <span className="w-3 h-3 rounded-sm" style={{background: m.color}}/>
                  {m.name}
                </td>
                <td className="text-right font-mono">{m.pct}%</td>
                <td className="text-right font-mono">{m.rpm}</td>
                <td className="text-right"><span className="n-chip">reserved</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function AuditPage() {
  const [filter, setFilter] = useState("all");
  const [q, setQ] = useState("");
  const list = demoAuditLog.filter(e => (filter==="all" || e.scope===filter) && (e.actor+e.action).toLowerCase().includes(q.toLowerCase()));
  const exportCsv = () => {
    const rows = [["at","actor","action","scope","status"], ...list.map(e=>[e.at,e.actor,e.action,e.scope,e.status])];
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([rows.map(r=>r.map(c=>`"${c}"`).join(",")).join("\n")], {type:"text/csv"}));
    a.download = "noetaris-audit-demo.csv"; a.click();
    toast.success(`Exported ${list.length} audit rows (DEMO_FIXTURE)`);
  };
  return (
    <div className="p-4 md:p-8" data-testid="audit-page">
      <PageHeader title="Audit & Approvals" eyebrow="LIVE_VERIFIED (demo)" action={
        <button onClick={exportCsv} className="n-btn-ghost h-9 px-4 flex items-center gap-2 text-xs" data-testid="audit-export-btn"><Icons.Download size={12}/> Export CSV</button>
      }>
        Every mutation routes through server-side authority. The log below is DEMO fixture to showcase layout.
      </PageHeader>
      <input value={q} onChange={(e)=>setQ(e.target.value)} placeholder="Search actor or action…" className="n-glass rounded-xl h-10 px-4 text-sm w-full sm:w-80 mb-3 outline-none" data-testid="audit-search-input"/>
      <div className="flex gap-2 mb-4 text-xs">
        {["all","identity","workflow","knowledge","source","agent","budget"].map(k=>(
          <button key={k} onClick={()=>setFilter(k)} className={"n-chip " + (filter===k?"":"opacity-60")} data-testid={`audit-filter-${k}`}>{k}</button>
        ))}
      </div>
      <div className="n-glass rounded-2xl overflow-x-auto">
        <table className="w-full text-sm min-w-[640px]">
          <thead>
            <tr className="text-[color:var(--n-text-subtle)] text-[11px] uppercase tracking-widest">
              <th className="text-left py-3 px-4 font-normal">At</th>
              <th className="text-left px-4 font-normal">Actor</th>
              <th className="text-left px-4 font-normal">Action</th>
              <th className="text-left px-4 font-normal">Scope</th>
              <th className="text-left px-4 font-normal">Status</th>
            </tr>
          </thead>
          <tbody>
            {list.length===0 && <tr><td colSpan={5} className="py-8 text-center text-sm text-[color:var(--n-text-subtle)]">No audit events match.</td></tr>}
            {list.map((e)=>(
              <tr key={e.id} className="border-t border-[color:var(--n-stroke-soft)] hover:bg-[rgba(46,155,255,0.03)]">
                <td className="py-2.5 px-4 font-mono text-xs">{new Date(e.at).toLocaleString()}</td>
                <td className="px-4 font-mono text-xs">{e.actor}</td>
                <td className="px-4">{e.action}</td>
                <td className="px-4"><span className="n-chip text-[10px]">{e.scope}</span></td>
                <td className="px-4"><span className={"n-chip text-[10px] " + (e.status==="LIVE_RESTRICTED"?"n-chip-amber":"n-chip-green")}>{e.status}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function GovernancePage() {
  return (
    <div className="p-4 md:p-8" data-testid="governance-page">
      <PageHeader title="Governance & Security" eyebrow="Scopes · policies">
        Server-side authority. The UI reflects state truthfully — read-only in demo mode.
      </PageHeader>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {[
          { k:"Identity scopes", v:"Local-token / Google / GitHub", s:"ready" },
          { k:"Source admission", v:"Private corpora 503 pending qualification", s:"restricted" },
          { k:"Model admission", v:"GPT-5 · Claude · Gemini · Local reserved", s:"ready" },
          { k:"Budget policy", v:"Per-user caps · reserved outcomes", s:"ready" },
          { k:"Retention policy", v:"Immutable source hashes · revisions tracked", s:"ready" },
          { k:"Approvals", v:"Human-in-the-loop for governed-run nodes", s:"ready" },
        ].map((p)=>(
          <div key={p.k} className="n-glass rounded-2xl p-5">
            <div className="flex items-center justify-between">
              <div className="text-sm">{p.k}</div>
              <span className={"n-chip " + (p.s==="restricted"?"n-chip-amber":"n-chip-green")}>{p.s}</span>
            </div>
            <div className="text-xs text-[color:var(--n-text-mute)] mt-2">{p.v}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

export { default as SettingsPage } from "./SettingsPage";

export function NotificationsPage() {
  const outlet = useOutletContext();
  if (mode === "live") {
    return (
      <section className="p-4 md:p-8" role="status" data-testid="notifications-page">
        <PageHeader title="Notifications" eyebrow="LIVE FEED UNAVAILABLE" />
        <p className="n-glass max-w-3xl rounded-xl p-6 text-sm text-[color:var(--n-text-mute)]">
          A live notification feed is not configured. No sample notifications are shown.
        </p>
      </section>
    );
  }
  const { notifications: items, setNotifications: setItems } = outlet;
  return (
    <div className="p-4 md:p-8" data-testid="notifications-page">
      <PageHeader title="Notifications" eyebrow="Streams · toasts · persistent" action={
        items.length > 0 && <button onClick={()=>setItems([])} className="n-btn-ghost h-9 px-4 text-xs" data-testid="notif-clear-all">Mark all read</button>
      }/>
      <ul className="space-y-3 max-w-3xl">
        {items.length===0 && <li className="n-glass rounded-xl p-6 text-sm text-center text-[color:var(--n-text-subtle)]">All caught up.</li>}
        {items.map((n)=>(
          <li key={n.id} className="n-glass rounded-xl p-4 flex items-start gap-3">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{
              background: n.kind==="err"?"rgba(242,79,97,0.14)": n.kind==="warn"?"rgba(242,179,94,0.14)": n.kind==="ok"?"rgba(72,199,161,0.14)":"rgba(46,155,255,0.14)",
              color: n.kind==="err"?"var(--n-red)": n.kind==="warn"?"var(--n-amber)": n.kind==="ok"?"var(--n-green)":"var(--n-cyan)"
            }}>
              {n.kind==="err"?<Icons.AlertTriangle size={14}/>: n.kind==="warn"?<Icons.AlertCircle size={14}/>: n.kind==="ok"?<Icons.CheckCircle2 size={14}/>:<Icons.Info size={14}/>}
            </div>
            <div className="flex-1">
              <div className="text-sm">{n.title}</div>
              <div className="text-xs text-[color:var(--n-text-subtle)]">{n.at}</div>
            </div>
            <button onClick={()=>setItems(x=>x.filter(i=>i.id!==n.id))} className="n-btn-ghost text-xs h-7 px-3" data-testid={`notif-dismiss-${n.id}`}>Dismiss</button>
          </li>
        ))}
      </ul>
    </div>
  );
}

// Generic stub for the many "stub" routes required by the IA
export function StubPage({ title, eyebrow, hint, tiles = [] }) {
  return (
    <div className="p-4 md:p-8" data-testid={`page-${title.toLowerCase().replace(/[^a-z]/g,'')}`}>
      <PageHeader title={title} eyebrow={eyebrow || "CONTRACT_READY"} action={
        <span className="n-chip-amber n-chip">BLOCKED_BACKEND</span>
      }>
        {hint || "This surface is designed and reachable. The matching backend contract is listed in /docs for Codex integration."}
      </PageHeader>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {(tiles.length?tiles:["Primary action","Secondary action","Related inspector","Streaming log","Governance anchor","Export"]).map((t)=>(
          <div key={t} className="n-glass rounded-2xl p-5 min-h-[150px] flex flex-col">
            <div className="text-xs text-[color:var(--n-text-subtle)] uppercase tracking-widest">Panel</div>
            <div className="text-sm mt-2">{t}</div>
            <div className="n-animate-sheen rounded-md mt-auto h-10"/>
          </div>
        ))}
      </div>
    </div>
  );
}

export function ModelsPage() {
  return (
    <div className="p-4 md:p-8" data-testid="models-page">
      <PageHeader title="Model Routing" eyebrow="DEMO_FIXTURE">
        Routes requests across providers based on policy, cost and availability.
      </PageHeader>
      <div className="n-glass rounded-2xl p-5">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {demoModels.map((m)=>(
            <div key={m.name} className="n-panel rounded-xl p-4 flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg flex items-center justify-center font-display text-sm" style={{background: m.color+"22", border:`1px solid ${m.color}66`, color: m.color}}>{m.name.split(" ")[0].slice(0,2)}</div>
              <div className="flex-1 min-w-0">
                <div className="text-sm">{m.name}</div>
                <div className="text-[11px] text-[color:var(--n-text-subtle)]">{m.rpm}</div>
              </div>
              <div className="w-32 h-1.5 rounded-full bg-[rgba(255,255,255,0.05)] overflow-hidden">
                <div className="h-full rounded-full" style={{width: m.pct+"%", background: m.color}}/>
              </div>
              <span className="font-mono text-xs text-[color:var(--n-text-mute)] w-10 text-right">{m.pct}%</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export function ObservabilityPage() {
  return (
    <div className="p-4 md:p-8" data-testid="observability-page">
      <PageHeader title="Observability" eyebrow="Streams · logs · traces"/>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {["Requests / min","Error rate","Latency p95","Tokens / min"].map((k,i)=>(
          <div key={k} className="n-glass rounded-2xl p-5">
            <div className="flex items-center justify-between mb-3">
              <div>
                <div className="text-[11px] uppercase tracking-widest text-[color:var(--n-text-subtle)]">{k}</div>
                <div className="font-display text-3xl mt-1">{["742K","0.12%","320 ms","8.4M"][i]}</div>
              </div>
              <span className={"n-chip "+(i===1?"n-chip-amber":"n-chip-green")}>{["+28%","-42%","-18%","+31%"][i]}</span>
            </div>
            <Sparkline data={Array.from({length:40}).map((_,n)=>Math.round(50+Math.sin(n/3+i)*20+n*0.6))} w={520} h={64} />
          </div>
        ))}
      </div>
      <div className="mt-6"><LogViewer height="h-72" /></div>
    </div>
  );
}

export function AgentsPage() {
  return (
    <div className="p-4 md:p-8" data-testid="agents-page">
      <PageHeader title="Agent Catalog" eyebrow="Build" action={
        <Link to="/app/agents/new" className="n-cta h-9 px-4 flex items-center gap-2 text-xs" data-testid="new-agent-btn"><Icons.Plus size={12}/> New agent</Link>
      }/>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {demoAgents.map((a)=>(
          <Link to={`/app/agents/${a.id}`} key={a.id} className="block n-glass rounded-2xl p-5 hover:-translate-y-0.5 transition-transform" data-testid={`agent-card-${a.id}`}>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-[rgba(46,155,255,0.1)] border border-[rgba(46,155,255,0.3)] flex items-center justify-center"><Icons.Bot size={16}/></div>
              <div className="flex-1 min-w-0">
                <div className="text-sm">{a.name}</div>
                <div className="text-[10px] uppercase tracking-widest text-[color:var(--n-text-subtle)]">{a.role}</div>
              </div>
              <span className={"n-chip " + (a.status==="Error"?"n-chip-red": a.status==="Running"?"n-chip-green":"n-chip-amber")}>{a.status}</span>
            </div>
            <div className="mt-4 text-xs text-[color:var(--n-text-mute)]">{a.model}</div>
            <div className="mt-3 h-1.5 rounded-full bg-[rgba(255,255,255,0.05)] overflow-hidden">
              <div className="h-full" style={{width:a.util+"%", background: a.status==="Error"?"var(--n-red)":"linear-gradient(90deg,#2E9BFF,#5ED6ED)"}}/>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

export function WorkflowsPage() {
  return (
    <div className="p-4 md:p-8" data-testid="workflows-page">
      <PageHeader title="Workflow Catalog" eyebrow="Build" action={
        <Link to="/app/workflows/new" className="n-cta h-9 px-4 flex items-center gap-2 text-xs" data-testid="new-workflow-btn"><Icons.Plus size={12}/> New workflow</Link>
      }/>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {demoWorkflows.map((w)=>(
          <Link to="/app/workflows/wf-sample/edit" key={w.id} className="block n-glass rounded-2xl p-5 hover:-translate-y-0.5 transition-transform" data-testid={`workflow-card-${w.id}`}>
            <div className="flex items-center justify-between">
              <div className="text-sm">{w.name}</div>
              <span className="n-chip text-[10px]">{w.id}</span>
            </div>
            <div className="mt-3 h-1.5 rounded-full bg-[rgba(255,255,255,0.05)] overflow-hidden">
              <div className="h-full rounded-full" style={{width: Math.max(2,w.progress)+"%", background: w.color==="red"?"var(--n-red)": w.color==="amber"?"var(--n-amber)": w.color==="muted"?"var(--n-text-subtle)":"linear-gradient(90deg,#2E9BFF,#5ED6ED)"}}/>
            </div>
            <div className="mt-2 text-xs text-[color:var(--n-text-subtle)]">{w.eta}</div>
          </Link>
        ))}
      </div>
    </div>
  );
}
