import React, { useEffect, useState } from "react";
import { Lock, RotateCcw, FlaskConical } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "./OperationsPages";

const KEY = "noetaris.demo.sim";
const DEFAULTS = { model: "GPT-5 reserved", voice: "en-US", density: "comfortable", scenario: "normal", reduceMotion: false };
const SCENARIOS = [["normal", "Normal"], ["provider-outage", "Provider outage"], ["budget-near-cap", "Budget near cap"], ["restricted-user", "Restricted user"]];
const LOCKED = ["Global model provisioning", "Provider credentials", "Permission policies", "Retention policy", "Sandbox / network isolation", "Paid execution controls"];

function Select({ k, opts, value, onChange }) {
  return (
    <select value={value} onChange={(e) => onChange(k, e.target.value)} className="h-9 px-2 rounded-lg n-glass text-sm outline-none bg-[color:var(--n-bg-elev)]" data-testid={`demo-${k}-select`}>
      {opts.map((o) => <option key={o}>{o}</option>)}
    </select>
  );
}

export default function DemoControlsPage() {
  const [s, setS] = useState(() => { try { return { ...DEFAULTS, ...JSON.parse(sessionStorage.getItem(KEY)) }; } catch { return DEFAULTS; } });
  useEffect(() => {
    try { sessionStorage.setItem(KEY, JSON.stringify(s)); } catch { /* storage restricted */ }
    document.documentElement.dataset.reduceMotion = s.reduceMotion ? 'true' : 'false';
    window.dispatchEvent(new Event('noetaris-motion-change'));
  }, [s]);
  const set = (k, v) => setS((p) => ({ ...p, [k]: v }));


  return (
    <div className="p-4 md:p-8 max-w-5xl" data-testid="demo-controls-page">
      <PageHeader title="Safe Demo Controls" eyebrow="Per-user · session only" action={
        <button onClick={() => { setS(DEFAULTS); toast.success("Simulation reset"); }} className="n-btn-ghost h-9 px-4 text-xs flex items-center gap-2" data-testid="demo-reset-btn"><RotateCcw size={12} />Reset</button>
      }>
        <span className="n-chip n-chip-amber mr-2">Preview simulation — no backend policy changed</span> Stored in this tab only and cleared on sign-out.
      </PageHeader>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="n-glass rounded-2xl p-5 space-y-4">
          <div className="text-[11px] uppercase tracking-widest text-[color:var(--n-text-subtle)]">Your preferences</div>
          {[["Personal model default", "model", ["GPT-5 reserved", "Claude Sonnet 5.5", "Gemini 3 Flash", "Local / AMD"]], ["Voice language", "voice", ["en-US", "en-GB", "es-ES", "de-DE"]], ["Density", "density", ["comfortable", "compact"]]].map(([l, k, o]) => (
            <div key={k} className="flex items-center justify-between gap-4"><span className="text-sm">{l}</span><Select k={k} opts={o} value={s[k]} onChange={set} /></div>
          ))}
          <div className="flex items-center justify-between"><span className="text-sm">Reduce motion preview</span>
            <button aria-label="Reduce interface motion" aria-pressed={s.reduceMotion} onClick={() => set("reduceMotion", !s.reduceMotion)} className={"w-11 h-6 rounded-full relative transition-colors " + (s.reduceMotion ? "bg-[color:var(--n-blue)]" : "bg-[color:var(--n-stroke-strong)]")} data-testid="demo-reduce-motion-toggle">
              <span className="absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform" style={{ transform: s.reduceMotion ? "translateX(20px)" : "none" }} />
            </button>
          </div>
        </div>
        <div className="n-glass rounded-2xl p-5">
          <div className="text-[11px] uppercase tracking-widest text-[color:var(--n-text-subtle)] mb-3 flex items-center gap-2"><FlaskConical size={12} />Local scenario simulation</div>
          <div className="grid grid-cols-2 gap-2">
            {SCENARIOS.map(([k, l]) => (
              <button key={k} onClick={() => { set("scenario", k); toast.message(`Simulating “${l}” locally`); }} className={"p-3 rounded-xl text-sm text-left border transition-colors " + (s.scenario === k ? "border-[rgba(46,155,255,0.5)] bg-[rgba(46,155,255,0.1)]" : "border-[color:var(--n-stroke-soft)] hover:bg-[rgba(233,239,246,0.03)]")} data-testid={`demo-scenario-${k}`}>{l}</button>
            ))}
          </div>
          <div className="text-[11px] text-[color:var(--n-text-subtle)] mt-3">Active: <span className="font-mono text-[color:var(--n-cyan)]">{s.scenario}</span> · shown as a banner across the app and reflected in Command Center health.</div>
        </div>
        <div className="n-glass rounded-2xl p-5 lg:col-span-2">
          <div className="text-[11px] uppercase tracking-widest text-[color:var(--n-text-subtle)] mb-3">Global controls · read-only in demo profile</div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {LOCKED.map((l) => (
              <div key={l} className="n-panel rounded-xl p-3 flex items-center gap-3 opacity-80" title="Requires separately permission-gated operator console">
                <Lock size={14} className="text-[color:var(--n-red)]" /><span className="text-sm">{l}</span><span className="ml-auto n-chip n-chip-red text-[9px]">RESTRICTED</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
