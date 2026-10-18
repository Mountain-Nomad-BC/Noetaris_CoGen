import React, { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';
import { apiRequest, changeProof, mode } from '../services/api';
const Context = createContext(null);
const initial = { status: 'loading', identity: null, capabilities: null, providers: {}, error: null };
const cleanup = () => window.dispatchEvent(new Event('noetaris-identity-cleared'));
function identity(value) {
  if (!value || typeof value.actor !== 'string' || typeof value.role !== 'string') throw new Error('Unrecognized canonical identity');
  return value;
}
export function AuthProvider({ children }) {
  const [state, setState] = useState(initial);
  const current = useRef({ epoch: 0, bearer: null, csrf: null, providers: {}, logoutPending: false });
  const channel = useRef(null);
  const clear = useCallback(() => {
    const version = ++current.current.epoch;
    changeProof(); cleanup();
    setState({ ...initial, providers: current.current.providers });
    return version;
  }, []);
  const refresh = useCallback(async (bearer = current.current.bearer) => {
    if (current.current.logoutPending) return;
    if (mode === 'demo') { setState({ ...initial, status: 'demo' }); return; }
    // The browser auth UI never persists or embeds API bearer credentials.
    const activeBearer = bearer;
    const version = clear(); current.current.bearer = activeBearer;
    try {
      const config = await apiRequest('/auth/config', { auth: false });
      if (version !== current.current.epoch) return;
      if (!config.providers || typeof config.providers.google !== 'boolean' || typeof config.providers.github !== 'boolean') throw new Error('Unrecognized authentication configuration');
      current.current.providers = config.providers; current.current.csrf = config.csrf;
      changeProof({ bearer: activeBearer, csrf: config.csrf });
      if (activeBearer) {
        const caps = await apiRequest('/v1/capabilities');
        if (version !== current.current.epoch) return;
        const who = identity(caps.identity);
        changeProof({ bearer: activeBearer, csrf: config.csrf, actor: who.actor });
        setState({ status: 'authenticated', identity: who, capabilities: caps, providers: config.providers, error: null }); return;
      }
      if (!config.csrf) {
        setState({ ...initial, status: 'anonymous', providers: config.providers }); return;
      }
      const session = await apiRequest('/auth/session', { auth: false });
      if (version !== current.current.epoch) return;
      const who = identity(session.identity);
      if (typeof session.csrf !== 'string') throw new Error('Missing session CSRF proof');
      current.current.csrf = session.csrf; changeProof({ csrf: session.csrf, actor: who.actor });
      const caps = await apiRequest('/v1/capabilities');
      if (version !== current.current.epoch) return;
      if (identity(caps.identity).actor !== who.actor) throw new Error('Canonical identity changed');
      setState({ status: 'authenticated', identity: who, capabilities: caps, providers: config.providers, error: null });
    } catch (error) {
      if (version !== current.current.epoch || error.name === 'AbortError') return;
      changeProof({ csrf: current.current.csrf }); cleanup();
      if (error.status === 401) current.current.bearer = null;
      setState({ ...initial, providers: current.current.providers, status: error.status === 401 ? 'anonymous' : 'error', error: error.message });
    }
  }, [clear]);
  const loginLocal = useCallback(async token => {
    if (typeof token !== 'string' || !token.trim()) throw new Error('Enter an existing local credential');
    await refresh(token.trim());
  }, [refresh]);
  const startOAuth = useCallback(async (provider, intent = 'login') => {
    if (!['google', 'github'].includes(provider) || !['login', 'signup', 'link'].includes(intent)) throw new Error('Unsupported identity operation');
    if (!current.current.providers[provider]) throw new Error('Provider is not configured');
    const result = await apiRequest(`/auth/${provider}/start`, { method: 'POST', body: { mode: intent } });
    const url = new URL(result.authorization_url);
    const expected = provider === 'google' ? 'https://accounts.google.com/o/oauth2/v2/auth' : 'https://github.com/login/oauth/authorize';
    if (url.origin + url.pathname !== expected || url.username || url.password || url.hash) throw new Error('Unexpected provider authorization destination');
    window.location.assign(url.href);
  }, []);
  const logout = useCallback(async () => {
    current.current.logoutPending = true;
    const bearer = current.current.bearer; const version = clear();
    channel.current?.postMessage('identity-cleared');
    changeProof({ bearer, csrf: current.current.csrf });
    try {
      if (current.current.csrf) await apiRequest('/auth/logout', { method: 'POST' });
      if (version !== current.current.epoch) return false;
      current.current.bearer = null; current.current.csrf = null; changeProof(); cleanup();
      current.current.logoutPending = false;
      setState({ ...initial, status: 'anonymous', providers: current.current.providers });
      // Establish the new anonymous browser/CSRF binding before other tabs read it.
      await refresh(null);
      channel.current?.postMessage('identity-changed');
      return true;
    } catch (error) {
      if (version !== current.current.epoch) return false;
      changeProof();
      setState({ ...initial, status: 'logout-unconfirmed', providers: current.current.providers, error: 'Server sign-out is unconfirmed. Retry sign-out before leaving this browser.' });
      channel.current?.postMessage('logout-unconfirmed');
      return false;
    }
  }, [clear, refresh]);
  useEffect(() => {
    refresh();
    const visible = () => { if (document.visibilityState === 'visible') refresh(); };
    const expired = () => refresh();
    document.addEventListener('visibilitychange', visible);
    window.addEventListener('noetaris-auth-expired', expired);
    if (typeof BroadcastChannel !== 'undefined') {
      const bc = new BroadcastChannel('noetaris.identity.v1'); channel.current = bc;
      bc.onmessage = event => {
        if (event.data === 'identity-cleared') {
          current.current.logoutPending = true; current.current.bearer = null; clear();
        } else if (event.data === 'identity-changed') {
          current.current.logoutPending = false; refresh();
        } else if (event.data === 'logout-unconfirmed') {
          current.current.logoutPending = true;
          setState({ ...initial, status: 'logout-unconfirmed', providers: current.current.providers, error: 'Server sign-out is unconfirmed. Retry sign-out before leaving this browser.' });
        }
      };
    }
    return () => { ++current.current.epoch; changeProof(); document.removeEventListener('visibilitychange', visible); window.removeEventListener('noetaris-auth-expired', expired); channel.current?.close(); };
  }, [refresh]);
  return <Context.Provider value={{ ...state, refresh, loginLocal, startOAuth, logout }}>{children}</Context.Provider>;
}
export function useAuth() { const value = useContext(Context); if (!value) throw new Error('AuthProvider is required'); return value; }
