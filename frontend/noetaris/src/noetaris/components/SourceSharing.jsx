import React, { useEffect, useRef, useState } from 'react';
import { apiRequest } from '../services/api';
import { accessSnapshot, shareRequest } from '../services/sourceControls';

export default function SourceSharing({ source, identity }) {
  const allowed = identity.identity_kind === 'local-user' && source.can_manage_access === true;
  const [state, setState] = useState({ busy: false, snapshot: null, error: null, notice: null });
  const [target, setTarget] = useState(''); const [kind, setKind] = useState('user'); const [expiry, setExpiry] = useState('');
  const pending = useRef(null); const epoch = useRef(0);
  useEffect(() => () => { ++epoch.current; pending.current?.abort(); }, []);
  async function reload() {
    const version = ++epoch.current; pending.current?.abort();
    const controller = new AbortController(); pending.current = controller;
    setState({ busy: true, snapshot: null, error: null, notice: null });
    try {
      const snapshot = accessSnapshot(await apiRequest(`/v1/sources/${source.id}/access`, { signal: controller.signal }),source.id,identity.actor);
      if (version === epoch.current) setState({ busy: false, snapshot, error: null, notice: null });
    } catch (error) { if (version === epoch.current && error.name !== 'AbortError') setState({ busy: false, snapshot: null, error: error.message, notice: null }); }
  }
  async function mutate(values) {
    if (state.busy || !state.snapshot) return;
    let request;
    try { request = shareRequest(state.snapshot,values); }
    catch (error) { setState(previous => ({ ...previous, error: error.message, notice: null })); return; }
    const version = ++epoch.current; pending.current?.abort();
    const controller = new AbortController(); pending.current = controller;
    setState({ busy: true, snapshot: null, error: null, notice: null });
    try {
      const changed = await apiRequest(`/v1/sources/${source.id}/access`, { method: 'POST', body: request, signal: controller.signal });
      if (changed.document_id !== source.id || changed.state !== (values.revoke ? 'revoked' : 'shared') || !Number.isSafeInteger(changed.epoch) || changed.epoch <= request.expected_epoch)
        throw new Error('Sharing mutation was not confirmed. Reload current owner state.');
      const snapshot = accessSnapshot(await apiRequest(`/v1/sources/${source.id}/access`, { signal: controller.signal }),source.id,identity.actor);
      if (version === epoch.current) setState({ busy: false, snapshot, error: null, notice: values.revoke ? 'Revocation confirmed by the server.' : 'Read grant confirmed by the server.' });
    } catch (error) {
      if (version === epoch.current && error.name !== 'AbortError') setState({ busy: false, snapshot: null, error: `${error.message} Reload current sharing state before another change.`, notice: null });
    }
  }
  if (!allowed) return <p className="text-sm" data-testid="source-sharing-withheld">Sharing management requires admitted individual owner access.</p>;
  return <section className="n-panel rounded-xl p-4 space-y-3" data-testid="source-sharing">
    <h3 className="font-display text-xl">Private source sharing</h3>
    <p>Only the current owner can grant or revoke read access. Enter exact known user/group identifiers; no account directory is exposed.</p>
    <button type="button" disabled={state.busy} onClick={reload} className="n-btn-ghost p-2">Load current owner grants</button>
    {state.error && <p role="alert">{state.error}</p>}
    {state.notice && <p role="status">{state.notice}</p>}
    {state.snapshot && <>
      <p className="break-all">Owner: {state.snapshot.owner} · policy epoch {state.snapshot.epoch}</p>
      <form className="grid grid-cols-1 sm:grid-cols-2 gap-3" onSubmit={event => { event.preventDefault(); mutate({ kind, target, expiry }); }}>
        <label>Subject type<select className="block w-full n-glass p-2" value={kind} onChange={event => setKind(event.target.value)}><option value="user">User</option><option value="group">Group</option></select></label>
        <label>Exact identifier<input className="block w-full n-glass p-2" maxLength={128} value={target} onChange={event => setTarget(event.target.value)} /></label>
        <label className="sm:col-span-2">Optional future expiry (ISO timestamp with timezone)<input className="block w-full n-glass p-2" value={expiry} onChange={event => setExpiry(event.target.value)} placeholder="2027-01-01T12:00:00Z" /></label>
        <button disabled={state.busy} className="n-cta p-2 rounded" type="submit">Grant read access</button>
      </form>
      <ul>{state.snapshot.grants.map(row => <li className="n-glass p-3 rounded-lg mt-2 break-all" key={`${row.subject_kind}:${row.subject_id}`}>
        {row.subject_kind}: {row.subject_id} · {row.revoked ? 'revoked' : 'not revoked'} · expiry: {row.expires_at || 'none'}
        <button type="button" className="n-btn-ghost p-2" disabled={state.busy || row.revoked} onClick={() => mutate({ kind: row.subject_kind, target: row.subject_id, revoke: true })}>Revoke read grant</button>
      </li>)}</ul>
      {!state.snapshot.grants.length && <p>No explicit read grants.</p>}
    </>}
  </section>;
}
