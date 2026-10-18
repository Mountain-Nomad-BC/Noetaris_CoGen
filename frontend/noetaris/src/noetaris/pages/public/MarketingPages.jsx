import React from "react";
import PublicHeader from "../../layout/PublicHeader";
import PublicFooter from "../../components/PublicFooter";
import { Link } from "react-router-dom";
import { ArrowRight, CheckCircle2, Minus } from "lucide-react";

export function MarketingPage({ title, eyebrow, sections, bullets = [] }) {
  return (
    <div className="min-h-screen" data-testid={`marketing-${title.toLowerCase()}`}>
      <PublicHeader />
      <section className="max-w-[1200px] mx-auto px-5 md:px-8 py-12 md:py-20">
        <div className="text-[11px] uppercase tracking-[0.3em] text-[color:var(--n-cyan)] mb-4">{eyebrow}</div>
        <h1 className="font-display text-4xl md:text-5xl mb-5">{title}</h1>
        <div className="n-divider mb-10"/>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
          <div>
            {sections.map((s) => (
              <section key={s.heading} className="mb-10">
                <h3 className="font-display text-xl mb-3">{s.heading}</h3>
                <p className="text-[color:var(--n-text-mute)] leading-relaxed text-[15px]">{s.body}</p>
              </section>
            ))}
          </div>
          <div className="n-glass rounded-2xl p-6 h-fit md:sticky md:top-24">
            <div className="text-[11px] uppercase tracking-widest text-[color:var(--n-text-subtle)] mb-3">Highlights</div>
            <ul className="space-y-3">
              {bullets.map((b) => (
                <li key={b.label} className="flex items-start gap-3 text-sm">
                  {b.ok ? <CheckCircle2 size={16} className="text-[color:var(--n-green)] mt-0.5"/> : <Minus size={16} className="text-[color:var(--n-amber)] mt-0.5"/>}
                  <span className="text-[color:var(--n-text-mute)]">{b.label}</span>
                </li>
              ))}
            </ul>
            <Link to="/login" className="n-cta mt-6 w-full h-11 flex items-center justify-center gap-2 text-sm">
              Check Sign-In Availability <ArrowRight size={14} />
            </Link>
          </div>
        </div>
      </section>
      <PublicFooter />
    </div>
  );
}

export const PlatformPage = () => (
  <MarketingPage title="Platform" eyebrow="Preview — not release certified"
    sections={[
      { heading: "A single operating environment", body: "Noetaris CoGen is designed to bring research, documents, agents, workflows, routing, costs and governance into one auditable surface. This local preview is not admitted for full-feature operation; protected actions remain unavailable." },
      { heading: "Honest telemetry", body: "The interface is intended to distinguish verified, restricted, fixture and unavailable data. A rendered screen is not evidence that a service or workflow is live." },
      { heading: "Composable agents", body: "Agent and workflow authoring are part of the design scope. Persistence, execution and AI-proposed changes are not release-qualified in this runtime." },
    ]}
    bullets={[
      { label: "Core document and review workflows have scoped local Docker checks", ok: false },
      { label: "Local authorized sign-in is implemented; real Google/GitHub configuration remains pending", ok: false },
      { label: "AMD hosted Gemma is selected; automatic dispatch, voice and Evolus remain incomplete", ok: false },
      { label: "Release admission is denied; do not use this as a live workspace", ok: false },
    ]}
  />
);

export const CapabilitiesPage = () => (
  <MarketingPage title="Capabilities" eyebrow="Capability preview — runtime unqualified"
    sections={[
      { heading: "Document intelligence", body: "Local browser workflows verify document upload, automatic indexing, original-byte download, PDF rendering, semantic retrieval and cited answers for synthetic fixtures. Broader format, quality, accessibility and production acceptance remain open." },
      { heading: "Authenticated chat and voice", body: "Chat access is protected by server identity and admission. Voice is deferred; no unified live timeline or cancellation behavior is claimed." },
      { heading: "Workflow authoring", body: "Authoring screens exist in the preview, but save, execute, retry and diff-review chains are not release-qualified." },
    ]}
    bullets={[
      { label: "Live model routing is not verified", ok: false },
      { label: "AMD hosted connectivity passes; Evolus is optional and not configured", ok: false },
      { label: "Read-only operational screens use real API projections with role checks", ok: false },
      { label: "Browser SQL access is intentionally unavailable", ok: false },
    ]}
  />
);

export const ArchitecturePage = () => (
  <MarketingPage title="Architecture" eyebrow="Target boundaries — not a deployment claim"
    sections={[
      { heading: "Boundaries", body: "The target design assigns identity, source bytes, citation geometry, job state, approvals, budgets and execution to server-side authority. Client-side presentation is not authorization." },
      { heading: "Transport", body: "HTTP requests, SSE streams and WebSockets must match the verified service contract; unused or unsupported transports are not evidence of an operational integration." },
      { heading: "Deployment", body: "The isolated six-service Docker integration is available on loopback port 8790. Target hosting is Firebase with an OCI API/database and AMD hosted inference. Public rollout, identity commissioning and release admission remain incomplete." },
    ]}
    bullets={[
      { label: "React + Vite frontend source builds successfully", ok: true },
      { label: "Release gate currently denies full-feature startup", ok: false },
      { label: "Direct database access from the browser is not permitted", ok: false },
      { label: "AMD / ROCm deployment is outside this qualification", ok: false },
    ]}
  />
);

export const DevelopersPage = () => (
  <MarketingPage title="Developers" eyebrow="Contracts first"
    sections={[
      { heading: "API Contract Register", body: "The source includes typed API adapters and contract checks. Only backend endpoints that pass current runtime and acceptance checks should be treated as available; see /docs." },
      { heading: "Backend gap register", body: "Outstanding work remains subject to the acceptance ledger and release gate. A present UI route does not establish an implemented or authorized API." },
    ]}
    bullets={[
      { label: "Frontend source and contract checks build", ok: true },
      { label: "Fixture labeling is distinct from live data", ok: true },
      { label: "OpenAPI import is not configured", ok: false },
    ]}
  />
);

export const DocsPage = () => (
  <MarketingPage title="Docs" eyebrow="Reading room"
    sections={[
      { heading: "Reference material", body: "Read the current implementation plan, acceptance ledger and deployment state. Archived route inventories and snapshots are historical references, not proof of current functionality." },
      { heading: "Design system", body: "Dark-first graphite/silver with electric blue and restrained red. Motion should reflect real state; decorative animation must not imply service health." },
    ]}
    bullets={[
      { label: "Design tokens published", ok: true },
      { label: "Motion guidelines", ok: true },
      { label: "Live SDK", ok: false },
    ]}
  />
);

export const ContactPage = () => (
  <MarketingPage title="Contact" eyebrow="Talk to engineering"
    sections={[
      { heading: "Qualification", body: "This preview does not accept contact requests, private corpora or credentials. Use an authorized project channel for qualification." },
      { heading: "Privacy", body: "Do not place sensitive documents or secrets in this preview. No data-residency or audit guarantee is made by this page." },
    ]}
    bullets={[
      { label: "No contact form or private-data upload is provided", ok: true },
      { label: "Residency and audit guarantees are not asserted", ok: false },
    ]}
  />
);
