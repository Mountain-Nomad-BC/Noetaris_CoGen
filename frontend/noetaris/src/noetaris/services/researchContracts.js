export function retrievalCoverageNotice(coverage) {
  if (!coverage || typeof coverage !== 'object' || Array.isArray(coverage)) return null;
  const notices = [];
  if (coverage.additional_matches_exist === true) {
    const counts = [
      coverage.matching_chunks_lower_bound,
      coverage.returned_chunks,
      coverage.omitted_chunks_at_least,
    ];
    if (counts.every(value => Number.isSafeInteger(value) && value >= 0)) {
      notices.push(`At least ${counts[0]} matching chunks; ${counts[1]} shown and at least ${counts[2]} omitted. Results are not exhaustive.`);
    } else {
      notices.push('Additional matching excerpts were omitted. Results are not exhaustive.');
    }
  }
  if (coverage.semantic_state === 'unavailable') {
    notices.push('Semantic retrieval is unavailable; these results use lexical matching only.');
  }
  return notices.length ? notices.join(' ') : null;
}
