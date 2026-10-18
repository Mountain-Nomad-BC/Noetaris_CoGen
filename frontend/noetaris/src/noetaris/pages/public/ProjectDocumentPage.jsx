import React from 'react';
import { Link } from 'react-router-dom';
import PublicHeader from '../../layout/PublicHeader';
import PublicFooter from '../../components/PublicFooter';
import { publicDocuments, documentVersion } from '../../content/publicDocuments';
export default function ProjectDocumentPage({ kind = 'docs' }) {
 const page = publicDocuments[kind];
 return <div className="min-h-screen" data-testid={`project-document-${kind}`}><PublicHeader />
  <main className="project-document max-w-4xl mx-auto px-5 py-12">
   <h1 className="font-display text-3xl md:text-4xl mb-4">{page.title}</h1>
   <p className="text-[color:var(--n-text-mute)]">{page.description}</p>
   <p className="text-sm mt-3">Document version: {documentVersion}</p>
   {page.draft && <p role="note" className="n-panel rounded-lg p-4 mt-5">Draft for operator and legal review. Required operator details and processing decisions are pending. Public personal-data collection is not approved by this document.</p>}
   <nav aria-label="On this page" className="flex flex-wrap gap-3 my-8">{page.sections.map(([heading], index) => <a className="underline text-sm" key={heading} href={`#section-${index}`}>{heading}</a>)}</nav>
   {page.sections.map(([heading, body], index) => <section className="mb-8 scroll-mt-24" id={`section-${index}`} key={heading}>
    <h2 className="font-display text-xl mb-3">{heading}</h2><p className="leading-relaxed text-[color:var(--n-text-mute)]">{body}</p>
   </section>)}
   <p className="mt-8"><Link to="/docs" className="underline">Project documentation</Link> - <Link to="/ai-transparency" className="underline">AI transparency</Link></p>
  </main><PublicFooter /></div>;
}
