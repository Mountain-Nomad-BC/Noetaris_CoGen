import React, { useState, useEffect, useRef } from 'react';
import { Search, Database, ExternalLink } from 'lucide-react';
import { apiRequest } from '../../services/api';
import { retrievalCoverageNotice } from '../../services/researchContracts';
import { PageHeader } from './OperationsPages';
import { Link } from 'react-router-dom';

export default function ResearchPage() {
  const [query, setQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [results, setResults] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [documentTotal, setDocumentTotal] = useState(0);
  const [documentsLoading, setDocumentsLoading] = useState(true);
  const [documentsError, setDocumentsError] = useState('');
  const [searchError, setSearchError] = useState('');
  const [retrievalCoverage, setRetrievalCoverage] = useState(null);
  const searchController = useRef(null);

  useEffect(() => {
    const controller = new AbortController();
    apiRequest('/v1/documents?limit=25', { signal: controller.signal })
      .then(response => {
        if (!Array.isArray(response.items) || response.items.some(item => !item || typeof item !== 'object' || Array.isArray(item))
          || !Number.isSafeInteger(response.total) || response.total < response.items.length) {
          throw new Error('The source list returned an unrecognized response.');
        }
        setDocuments(response.items);
        setDocumentTotal(response.total);
      })
      .catch(error => {
        if (error.name !== 'AbortError') setDocumentsError(error.message || 'Unable to load sources.');
      })
      .finally(() => {
        if (!controller.signal.aborted) setDocumentsLoading(false);
      });
    return () => controller.abort();
  }, []);

  useEffect(() => () => searchController.current?.abort(), []);

  const handleSearch = async (e) => {
    e?.preventDefault();
    if (!query.trim()) return;
    searchController.current?.abort();
    const controller = new AbortController();
    searchController.current = controller;
    setHasSearched(true);
    setSearching(true);
    setSearchError('');
    setResults([]);
    setRetrievalCoverage(null);
    try {
      const response = await apiRequest(`/v1/search?q=${encodeURIComponent(query.trim())}`, { signal: controller.signal });
      if (!Array.isArray(response.items) || response.items.some(item => !item || typeof item !== 'object' || Array.isArray(item))) {
        throw new Error('Search returned an unrecognized response.');
      }
      setResults(response.items);
      setRetrievalCoverage(response.retrieval_coverage && typeof response.retrieval_coverage === 'object'
        && !Array.isArray(response.retrieval_coverage)
        ? response.retrieval_coverage
        : null);
    } catch (error) {
      if (error.name !== 'AbortError') setSearchError(error.message || 'Search failed.');
    } finally {
      if (!controller.signal.aborted) setSearching(false);
    }
  };

  const method = retrievalCoverage?.method;
  const coverageNotice = retrievalCoverageNotice(retrievalCoverage);
  const methodLabel = !hasSearched
    ? 'Search has not run'
    : !retrievalCoverage
      ? 'Retrieval metadata unavailable'
      : method === 'lexical'
        ? 'Lexical matches'
        : method === 'authorized-lexical-semantic-rank-fusion'
          ? 'Backend-reported lexical + semantic rank fusion'
          : 'Retrieval method not reported';

  return (
    <div className="p-4 md:p-8 max-w-6xl" data-testid="research-page">
      <PageHeader
        title="Research Search"
        eyebrow="Authorized source matches · Candidate excerpts"
      >
        Search accessible sources for relevant excerpts. Retrieval results are not verified answers, exhaustive coverage, or engineering determinations.
      </PageHeader>

      <form onSubmit={handleSearch} className="mb-8">
        <div className="n-glass rounded-2xl p-2 flex items-center gap-3 border border-[color:var(--n-stroke-soft)]">
          <Search size={18} className="text-slate-400 ml-3 shrink-0" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search terms in accessible source material"
            className="flex-1 bg-transparent border-none text-white text-sm placeholder:text-slate-500 focus:outline-none py-2"
            aria-label="Search accessible source material"
          />
          <button
            type="submit"
            disabled={searching || !query.trim()}
            className="n-cta px-5 py-2.5 rounded-xl text-xs font-semibold flex items-center gap-2 shrink-0 disabled:opacity-50"
          >
            <Search size={14} />
            <span>{searching ? "Searching…" : "Search"}</span>
          </button>
        </div>
      </form>

      {searchError && (
        <p className="mb-6 rounded-lg border border-rose-400/30 bg-rose-500/10 p-3 text-sm text-rose-200" role="alert">
          Search failed: {searchError}
        </p>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between text-xs text-slate-400 pb-2 border-b border-white/5">
            <span>Candidate excerpts ({results.length})</span>
            <span className="font-mono text-[10px]">{methodLabel}</span>
          </div>
          {coverageNotice && (
            <p className="rounded-lg border border-amber-300/30 bg-amber-500/10 p-3 text-sm text-amber-100"
              role="status" data-testid="retrieval-coverage">
              {coverageNotice}
            </p>
          )}

          {results.length > 0 ? (
            results.map((hit, idx) => {
              const documentId = typeof hit.document_id === 'string' && hit.document_id ? hit.document_id : null;
              const locator = typeof hit.locator === 'string' && hit.locator ? hit.locator : null;
              const excerpt = typeof hit.text === 'string' && hit.text
                ? hit.text
                : typeof hit.exact_quote === 'string' && hit.exact_quote
                  ? hit.exact_quote
                  : null;
              return (
                <div key={hit.id || `${documentId || 'match'}-${idx}`} className="n-glass rounded-xl p-4 border border-[color:var(--n-stroke-soft)] space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-[color:var(--n-blue)]" />
                      <span className="text-xs font-semibold text-white font-mono">
                        {typeof hit.id === 'string' && hit.id ? `[${hit.id}]` : `Match ${idx + 1}`}
                      </span>
                      <span className="text-[11px] px-2 py-0.5 rounded bg-white/5 text-slate-300 font-mono">
                        {typeof hit.projection_status === 'string' && hit.projection_status
                          ? hit.projection_status
                          : 'Review status not supplied'}
                      </span>
                    </div>
                    {documentId && (
                      <Link
                        to={`/app/documents/${encodeURIComponent(documentId)}`}
                        className="text-xs text-[color:var(--n-cyan)] flex items-center gap-1 hover:underline"
                      >
                        <span>Open source</span>
                        <ExternalLink size={11} />
                      </Link>
                    )}
                  </div>
                  <p className="break-words text-xs text-slate-300 leading-relaxed font-normal bg-black/20 p-3 rounded-lg border border-white/5">
                    {excerpt || 'Excerpt text is unavailable for this match.'}
                  </p>
                  <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono pt-1">
                    <span>Source: {documentId || 'Not supplied'}</span>
                    <span>Locator: {locator || 'Not supplied'}</span>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="n-glass rounded-xl p-10 text-center text-xs text-slate-400 space-y-3">
              <Search size={28} className="mx-auto text-slate-500 opacity-60" />
              <p>{searching
                ? 'Searching accessible sources…'
                : searchError
                  ? 'Results are unavailable because the search failed.'
                  : hasSearched
                    ? 'No matching excerpts were returned.'
                    : 'Submit a query to search accessible source material.'}</p>
            </div>
          )}
          {retrievalCoverage?.additional_matches_exist === true && (
            <p className="text-xs text-amber-200" role="status">
              More matching excerpts may exist; this result set is not exhaustive.
            </p>
          )}
          {['unavailable', 'not-configured'].includes(retrievalCoverage?.semantic_state) && (
            <p className="text-xs text-amber-200" role="status">
              Semantic retrieval is unavailable or not configured; these results use lexical matches only.
            </p>
          )}
        </div>

        <div className="space-y-4">
          <div className="n-glass rounded-xl p-4 border border-[color:var(--n-stroke-soft)] space-y-3">
            <h4 className="text-xs font-semibold text-white uppercase tracking-wider flex items-center gap-2">
              <Database size={14} className="text-[color:var(--n-cyan)]" />
              Sources
            </h4>
            {documentsError && (
              <p className="text-xs text-rose-200" role="alert">Unable to load sources: {documentsError}</p>
            )}
            {!documentsError && documentsLoading && (
              <p className="text-xs text-slate-400" role="status">Loading accessible sources…</p>
            )}
            {!documentsError && !documentsLoading && (
              <p className="text-xs text-slate-400">
                Showing {documents.length} of {documentTotal} accessible sources. Search results are not filtered to this list.
              </p>
            )}
            <div className="max-h-[400px] overflow-y-auto space-y-2 pr-1">
              {documents.map((doc, index) => {
                const sourceId = typeof doc.id === 'string' && doc.id ? doc.id : null;
                return (
                  <div key={sourceId || `${doc.title || 'source'}-${index}`} className="p-2.5 rounded-lg border bg-black/20 border-white/5">
                    {sourceId
                      ? <Link to={`/app/documents/${encodeURIComponent(sourceId)}`} className="block max-w-full text-xs font-medium text-white truncate hover:underline">
                          {doc.title || 'Untitled source'}
                        </Link>
                      : <div className="text-xs font-medium text-white truncate">{doc.title || 'Untitled source'}</div>}
                    <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono mt-1">
                      <span>Revision {doc.version || 'not supplied'}</span>
                      <span>{typeof doc.sha256 === 'string' ? doc.sha256.slice(0, 8) : 'Hash unavailable'}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
