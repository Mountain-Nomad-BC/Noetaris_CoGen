/** Exact-origin transport. Backend owns identity and permissions. */
import {deploymentRequest} from './deploymentOrigin.js';
const settings = import.meta.env || {};
export const mode = settings.VITE_NOETARIS_MODE === 'demo' ? 'demo' : 'live';
let proof = { bearer: null, csrf: null, actor: null };
let epoch = 0;
const active = new Set();
export class ApiError extends Error {
  constructor(status, message, requestId) {
    super(message); this.name = 'ApiError'; this.status = status; this.requestId = requestId;
  }
}
export function changeProof(next = {}) {
  epoch++;
  for (const controller of active) controller.abort();
  active.clear();
  proof = { bearer: null, csrf: null, actor: null, ...next };
}
function validPath(path) {
  if (typeof path !== 'string' || /[\\#\s]/.test(path) || /%(?:2e|2f|5c|00)/i.test(path.split('?')[0])) return false;
  if (/^\/auth\/(?:config|session|logout|(?:google|github)\/start)$/.test(path)) return true;
  return /^\/v1\/[a-zA-Z0-9/_?&=%.,:+-]+$/.test(path) && !path.split('?')[0].split('/').some(p => p === '.' || p === '..');
}
export async function apiRequest(path, { method = 'GET', body, signal, headers = {}, auth = true, responseType = 'json', maximumBytes } = {}) {
  if (mode !== 'live') throw new ApiError(0, 'Demo data is not a live backend.', null);
  if (!validPath(path)) throw new ApiError(0, 'Rejected API path', null);
  let destination;
  try { destination=deploymentRequest(path,settings); }
  catch { throw new ApiError(0,'Deployment API origin is not commissioned for this application.',null); }
  if(destination.crossOrigin&&auth&&proof.bearer)
    throw new ApiError(0,'Local bearer credentials cannot be sent to a remote deployment.',null);
  if (!['json', 'bytes'].includes(responseType)) throw new ApiError(0, 'Unsupported response type', null);
  if (responseType === 'bytes' && (!/^\/v1\/sources\/[a-f0-9]{32}\/original$/.test(path) || method !== 'GET'))
    throw new ApiError(0, 'Binary transport requires an original-source route', null);
  if (responseType === 'bytes' && (!Number.isSafeInteger(maximumBytes) || maximumBytes < 1 || maximumBytes > 32 * 1024 * 1024))
    throw new ApiError(0, 'Invalid original-source byte budget', null);
  const start = epoch;
  const controller = new AbortController();
  const cancel = () => controller.abort();
  if (signal?.aborted) controller.abort();
  signal?.addEventListener('abort', cancel, { once: true });
  active.add(controller);
  const timer = setTimeout(cancel, 300000);
  try {
    const supplied = new Headers(headers);
    for (const name of ['authorization', 'x-csrf-token', 'x-nsai-expected-actor']) {
      if (supplied.has(name)) throw new ApiError(0, 'Authentication headers are managed centrally.', null);
    }
    const multipart = typeof FormData !== 'undefined' && body instanceof FormData;
    if (body != null && !multipart) supplied.set('Content-Type', 'application/json');
    if (auth && proof.bearer) supplied.set('Authorization', `Bearer ${proof.bearer}`);
    if (auth && proof.actor) supplied.set('X-NSAI-Expected-Actor', proof.actor);
    if (!['GET', 'HEAD', 'OPTIONS'].includes(method.toUpperCase()) && proof.csrf) supplied.set('X-CSRF-Token', proof.csrf);
    const response = await fetch(destination.url, { method, credentials: destination.credentials, redirect: 'error', signal: controller.signal,
      headers: supplied, ...(body == null ? {} : { body: multipart ? body : JSON.stringify(body) }) });
    const requestId = response.headers.get('x-request-id');
    const type = response.headers.get('content-type') || '';
    let payload;
    if (response.ok && responseType === 'bytes') {
      const length = response.headers.get('content-length');
      if (length && Number(length) > maximumBytes) throw new ApiError(502, 'Original-source byte budget exceeded.', requestId);
      const reader = response.body?.getReader();
      if (!reader) throw new ApiError(502, 'Original-source streaming reader unavailable.', requestId);
      const chunks = []; let size = 0;
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          size += value.byteLength;
          if (size > maximumBytes) { await reader.cancel(); throw new ApiError(502, 'Original-source byte budget exceeded.', requestId); }
          chunks.push(value);
        }
      } finally { reader.releaseLock(); }
      const bytes = new Uint8Array(size); let offset = 0;
      for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
      payload = { bytes, mediaType: type };
    } else {
      try { payload = type.includes('application/json') ? await response.json() : null; }
      catch { throw new ApiError(502, 'Backend returned malformed JSON.', requestId); }
    }
    if (epoch !== start || controller.signal.aborted) throw new DOMException('Authentication or request changed', 'AbortError');
    if (!response.ok) {
      if (response.status === 401 && auth && proof.actor && typeof globalThis.dispatchEvent === 'function')
        globalThis.dispatchEvent(new Event('noetaris-auth-expired'));
      throw new ApiError(response.status,
        typeof payload?.detail === 'string' ? payload.detail : `Request failed (HTTP ${response.status})`, requestId);
    }
    if (payload == null) throw new ApiError(502, 'Expected a JSON backend response.', requestId);
    return payload;
  } finally {
    clearTimeout(timer); active.delete(controller); signal?.removeEventListener('abort', cancel);
  }
}
export async function submitChatTurn({ text, sessionId, documentId, signal }) {
  const payload = await apiRequest('/v1/chat', { method: 'POST', signal, body: {
    question: text, ...(sessionId && !sessionId.startsWith('local-') ? { session_id: sessionId } : {}),
    document_ids: documentId ? [documentId] : [],
  } });
  if (typeof payload?.answer !== 'string' || !Array.isArray(payload.citations) || typeof payload.session_id !== 'string')
    throw new ApiError(502, 'Unrecognized source-grounded chat response.', null);
  return { text: payload.answer, citations: payload.citations, sessionId: payload.session_id, turnId: null };
}
