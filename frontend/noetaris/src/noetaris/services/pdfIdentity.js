export async function sha256(bytes) {
  return [...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(value => value.toString(16).padStart(2,'0')).join('');
}
export function containedPdfRects(page, regions) {
  const valid = value => value && ['left','top','right','bottom','width','height'].every(key => Number.isFinite(value[key])) && value.width > 0 && value.height > 0;
  return valid(page) && Array.isArray(regions) && regions.length > 0 && regions.length <= 1000 && regions.every(rect => valid(rect) && rect.left >= page.left-1 && rect.top >= page.top-1 && rect.right <= page.right+1 && rect.bottom <= page.bottom+1);
}
export async function boundAnchor(anchor, source, pages) {
  if (!anchor) return null;
  if (anchor.schema !== 'nsai.citation-anchor/1' || anchor.document_id !== source.id || anchor.original_sha256 !== source.original_sha256 ||
      anchor.revision !== source.revision || !Number.isInteger(anchor.page) || anchor.page < 1 || anchor.page > pages ||
      anchor.selector?.type !== 'TextQuoteSelector' || typeof anchor.selector.exact !== 'string' || !anchor.selector.exact.trim() ||
      typeof anchor.quote_sha256 !== 'string' || !/^[a-f0-9]{64}$/.test(anchor.quote_sha256)) throw new Error('Citation does not match this original, revision or page.');
  const quote = new TextEncoder().encode(anchor.selector.exact);
  if (quote.byteLength > 64000 || await sha256(quote) !== anchor.quote_sha256) throw new Error('Citation quote integrity check failed.');
  return anchor;
}
