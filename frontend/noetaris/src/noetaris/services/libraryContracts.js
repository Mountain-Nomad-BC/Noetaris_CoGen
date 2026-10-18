/** Validate backend shape; never derive review/publication authority from indexing. */
export const sourceId = value => typeof value === 'string' && /^[a-f0-9]{32}$/.test(value);
const digest = value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
const index = value => value && typeof value === 'object' && !Array.isArray(value) && typeof value.state === 'string';
export function libraryPage(value) {
  if (!value || !Array.isArray(value.items) || value.items.length > 100 || !Number.isSafeInteger(value.total) || value.total < 0 ||
      typeof value.has_more !== 'boolean' || !(value.next_cursor === null || typeof value.next_cursor === 'string') ||
      value.has_more !== (typeof value.next_cursor === 'string' && value.next_cursor.length > 0) ||
      value.items.some(row => !sourceId(row.id) || typeof row.title !== 'string' || typeof row.version !== 'string' || !digest(row.sha256) || !index(row.indexing)))
    throw new Error('Unrecognized authorized library response');
  return value;
}
export function sourceRecord(value, expected) {
  if (!value || value.id !== expected || !sourceId(value.id) || typeof value.title !== 'string' || typeof value.revision !== 'string' ||
      !(value.original_sha256 === null || digest(value.original_sha256)) || !index(value.indexing) ||
      !(value.manifest === null || (typeof value.manifest === 'object' && !Array.isArray(value.manifest))) ||
      !(value.media_type === null || typeof value.media_type === 'string') || typeof value.raw_text !== 'string')
    throw new Error('Unrecognized source evidence response');
  return value;
}
export function uploadReceipt(value) {
  if (!value || !sourceId(value.document_id) || !digest(value.sha256) || typeof value.created !== 'boolean' || !index(value.indexing))
    throw new Error('Unrecognized durable upload receipt');
  return value;
}
export function uploadLimits(value) {
  if (!value || !Number.isSafeInteger(value.max_bytes) || value.max_bytes < 1 || value.max_bytes > 32 * 1024 * 1024 ||
      !Number.isSafeInteger(value.max_pages) || value.max_pages < 1 || !Number.isSafeInteger(value.max_chars) || value.max_chars < 1)
    throw new Error('Upload limits are unavailable or outside the frontend safety envelope');
  return value;
}

export function librarySearchResult(value){
 if(!value||!Array.isArray(value.items)||value.items.length>12||!value.retrieval_coverage||typeof value.retrieval_coverage.method!=='string'||!['ready','unavailable','not-configured'].includes(value.retrieval_coverage.semantic_state)||new Set(value.items.map(row=>row.id)).size!==value.items.length||value.items.some(row=>!row||typeof row.id!=='string'||!/^(?:[a-f0-9]{32}|[a-f0-9]{64})$/.test(row.id)||!sourceId(row.document_id)||typeof row.title!=='string'||row.title.length>2000||typeof row.revision!=='string'||typeof row.locator!=='string'||typeof row.text!=='string'||row.text.length>100000))throw new Error('Unrecognized authorized knowledge search result');
 return {items:value.items.map(row=>({id:row.id,document_id:row.document_id,title:row.title,revision:row.revision,locator:row.locator,text:row.text})),semantic_state:value.retrieval_coverage.semantic_state};
}
