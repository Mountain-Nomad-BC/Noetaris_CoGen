import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, FileText, Search, Shield } from 'lucide-react';
import PublicHeader from '../../layout/PublicHeader';
import PublicFooter from '../../components/PublicFooter';
export default function LandingPage() {
 return <div className="min-h-screen" data-testid="landing-page"><PublicHeader />
  <main className="max-w-6xl mx-auto px-5 md:px-8">
   <section className="py-16 md:py-24 grid lg:grid-cols-2 gap-12 items-start">
    <div><p className="text-sm uppercase tracking-widest text-[color:var(--n-text-mute)] mb-6">Engineering intelligence - RESEARCH CANDIDATE</p>
     <h1 className="font-display text-4xl md:text-6xl leading-tight mb-6">Research designed around your sources.</h1>
     <p className="leading-relaxed text-[color:var(--n-text-mute)] mb-8">Bring documents into a searchable workspace, inspect the evidence and ask source-based questions. Keep original files, extracted records and generated answers distinct.</p>
     <div className="flex flex-wrap gap-3"><Link to="/login" className="n-cta px-6 py-3 inline-flex gap-2 items-center" data-testid="hero-start-link">Check Access <ArrowRight size={16} /></Link><Link to="/docs" className="n-btn-ghost px-6 py-3" data-testid="hero-demo-link">Read the documentation</Link></div>
    </div>
    <div className="n-panel rounded-xl p-6"><h2 className="font-display text-xl mb-5">From document to evidence</h2>
     <ol className="space-y-5">{[
      ['01', 'Upload and index', 'Authorized uploads become extracted text, searchable passages and semantic records. Wait for the actual indexing status.'],
      ['02', 'Find and inspect', 'Use retrieval and the knowledge explorer, open the original and inspect its citations.'],
      ['03', 'Ask and review', 'AI-assisted answers remain subject to evidence checks and separate human review. Conflicts can withhold generation.']
     ].map(([n,title,body]) => <li className="flex gap-4" key={n}><span className="font-mono text-[color:var(--n-cyan)]">{n}</span><div><h3 className="font-medium mb-1">{title}</h3><p className="text-sm leading-relaxed text-[color:var(--n-text-mute)]">{body}</p></div></li>)}</ol>
    </div>
   </section>
   <section className="border-y border-[color:var(--n-stroke-soft)] py-8 mb-12" aria-label="Current availability"><h2 className="font-display text-xl mb-3">Current availability</h2><p className="leading-relaxed text-[color:var(--n-text-mute)]">Document ingestion, retrieval, citations, review and CPU Gemma answers have scoped local Docker verification. AMD hosted Gemma is the selected remote primary; integrated dispatch and free-provider fallback are still being completed. Public deployment and private-user content admission remain pending.</p><p className="mt-3 text-sm">AI outputs may be inaccurate. Verify sources. Indexing does not retrain model weights. <Link className="underline" to="/ai-transparency">Read the AI disclosure</Link>.</p></section>
   <section className="grid md:grid-cols-3 gap-5 pb-16">{[
    [FileText,'Source custody','Inspect retained originals and distinguish them from extracted or generated records.'],
    [Search,'Semantic retrieval','MiniLM supports passage retrieval; source references remain available for checking.'],
    [Shield,'Server authorization','Identity, access, review and release admission are enforced separately.']
   ].map(([Icon,title,body]) => <article key={title} className="n-panel rounded-xl p-6"><Icon size={22} className="mb-4" /><h2 className="font-display text-lg mb-3">{title}</h2><p className="text-sm leading-relaxed text-[color:var(--n-text-mute)]">{body}</p></article>)}</section>
  </main><PublicFooter /></div>;
}
