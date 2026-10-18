import React from 'react';
import { LayoutTemplate, ArrowRight, CheckCircle2, Shield, FileSearch, Sparkles, AlertTriangle } from 'lucide-react';
import { PageHeader } from './OperationsPages';
import { Link } from 'react-router-dom';

const TEMPLATES = [
  {
    id: "spec-verification",
    title: "Supplier Specification Verification Pipeline",
    desc: "Ingests multi-vendor PDF manuals, performs strict tabular extraction, anchors citation geometry, and flags conflicting tolerances against canonical baselines.",
    inputs: "PDF, XLSX, CSV specifications",
    stages: ["Parsing & OCR", "Geometry Anchoring", "Claim Extraction", "Conflict Quarantine"],
    action: "/app/library",
    actionLabel: "Launch Pipeline",
    badge: "RECOMMENDED",
  },
  {
    id: "multi-revision-audit",
    title: "Multi-Revision Discrepancy Audit",
    desc: "Compares engineering revisions across equipment lifecycles (e.g. Revision 1 vs Revision 2 temperature ratings) to identify superseded parameters without model hallucination.",
    inputs: "Sequential revisions of same equipment ID",
    stages: ["Revision Diffing", "Predicate Matching", "Independent Human Review", "Promotion Ledger"],
    action: "/app/knowledge/review",
    actionLabel: "Review Conflicts",
    badge: "GOVERNANCE",
  },
  {
    id: "hot-aisle-compliance",
    title: "Data Center Thermal & Clearance Compliance",
    desc: "Checks physical service clearances, hot-aisle containment specs, and 3-phase power requirements against facility standards.",
    inputs: "Rack and thermal service manuals",
    stages: ["Clearance Extraction", "Spatial Constraint Verification", "Evidence Sealing"],
    action: "/app/chat",
    actionLabel: "Query Standards",
    badge: "SAFETY",
  },
  {
    id: "ocr-quality-gate",
    title: "OCR Degradation & Quality Gate",
    desc: "Evaluates scan fidelity and character confidence scores. Automatically routes low-confidence scans (<0.85) to manual verification instead of automated indexing.",
    inputs: "Scanned legacy schematics",
    stages: ["Binarization Check", "Confidence Histogram", "Quarantine Flagging"],
    action: "/app/queue",
    actionLabel: "Inspect Queue",
    badge: "QUALITY",
  },
];

export default function TemplatesPage() {
  return (
    <div className="p-4 md:p-8 max-w-6xl" data-testid="templates-page">
      <PageHeader 
        title="Engineering Workflow Templates" 
        eyebrow="Orchestration · Reusable Pipelines · Quality Gates"
      >
        Standardized engineering verification workflows. Execute multi-document auditing, revision comparison, and compliance checks with full provenance tracking.
      </PageHeader>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {TEMPLATES.map((tmpl) => (
          <div key={tmpl.id} className="n-glass rounded-2xl p-6 border border-[color:var(--n-stroke-soft)] flex flex-col justify-between space-y-4">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="n-chip text-[10px] font-mono py-0.5">{tmpl.badge}</span>
                <span className="text-[11px] text-slate-400 font-mono">4 Stages</span>
              </div>
              <h3 className="font-display text-lg text-white">{tmpl.title}</h3>
              <p className="text-xs text-[color:var(--n-text-mute)] leading-relaxed">
                {tmpl.desc}
              </p>

              <div className="pt-2">
                <div className="text-[10px] uppercase font-mono text-slate-400 mb-1.5">Execution Stages:</div>
                <div className="flex flex-wrap gap-1.5">
                  {tmpl.stages.map((stg, i) => (
                    <span key={i} className="px-2 py-0.5 rounded-md bg-black/30 border border-white/5 text-[10px] text-slate-300 font-mono">
                      {i + 1}. {stg}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-white/5 flex items-center justify-between">
              <span className="text-[11px] text-slate-400 truncate max-w-[200px]">{tmpl.inputs}</span>
              <Link to={tmpl.action} className="n-cta px-4 py-2 text-xs flex items-center gap-1.5 font-semibold">
                <span>{tmpl.actionLabel}</span>
                <ArrowRight size={13} />
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
