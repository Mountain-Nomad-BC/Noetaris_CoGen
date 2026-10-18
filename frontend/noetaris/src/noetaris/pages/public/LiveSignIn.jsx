import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import Logo from '../../brand/Logo';
import { useAuth } from '../../state/AuthContext';

export default function LiveSignIn() {
  const auth = useAuth();
  const location = useLocation();
  const returned = new URLSearchParams(location.search).get('auth');
  const [token, setToken] = useState('');
  const [intent, setIntent] = useState('login');
  const [busy, setBusy] = useState(false);
  const [redirecting, setRedirecting] = useState(false);
  const [error, setError] = useState(null);
  const run = async action => {
    setBusy(true); setError(null);
    try { await action(); } catch (failure) { setError(failure.message); }
    finally { setBusy(false); }
  };
  const loading = busy || redirecting || auth.status === 'loading';
  const authenticated = auth.status === 'authenticated';
  const unconfirmed = auth.status === 'logout-unconfirmed';
  const localCredentialAllowed = ['localhost', '127.0.0.1', '[::1]'].includes(window.location.hostname);
  return <main className="min-h-screen flex items-center justify-center p-6" data-testid="login-page">
    <section className="n-glass rounded-2xl p-6 w-full max-w-xl space-y-5">
      <Link to="/"><Logo /></Link>
      <h1 className="font-display text-2xl">Sign in to Noetaris</h1>
      <p className="text-sm">Read the <Link className="underline" to="/terms">Terms</Link>, <Link className="underline" to="/privacy">Privacy notice</Link> and <Link className="underline" to="/ai-transparency">AI transparency notice</Link>. Signing in does not authorize private-content export.</p>
      <p className="text-sm">The server verifies sign-in. Private document access remains unavailable until separately admitted. Credentials remain in memory in this tab.</p>
      {returned === 'failed' && <p role="alert">Provider sign-in or account linking did not complete.</p>}
      {returned === 'cancelled' && <p role="status">Provider sign-in was cancelled.</p>}
      <p role="status" className="break-all" data-testid="auth-status" data-actor={auth.identity?.actor || ''}>{loading ? 'Checking server session…' : authenticated ? `Signed in as ${auth.identity.actor} (${auth.identity.role})` : 'No verified active identity'}</p>
      {(error || auth.error) && <p role="alert">{error || auth.error}</p>}
      {authenticated && <>
        <p data-testid="content-admission">{auth.capabilities?.content_access?.admitted === true ? 'Backend content admission is enabled for this identity.' : auth.capabilities?.content_access?.reason || 'Document access is not admitted.'}</p>
        <Link to="/app" className="n-cta inline-flex px-4 py-2">View integration status</Link>
      </>}
      {localCredentialAllowed && !authenticated && !unconfirmed && <form className="space-y-3" onSubmit={event => {
        event.preventDefault(); const credential = token; setToken(''); run(() => auth.loginLocal(credential));
      }}>
        <label className="block">Existing local credential
          <input type="password" autoComplete="off" value={token} onChange={event => setToken(event.target.value)} disabled={loading}
            className="block w-full n-panel rounded-lg p-3 mt-2" data-testid="login-password-input" />
        </label>
        <button type="submit" disabled={loading || !token.trim()} className="n-cta px-4 py-2 disabled:opacity-50" data-testid="login-submit-btn">Verify local identity</button>
      </form>}
      {redirecting && <p role="status" aria-live="polite">Opening the selected provider. Complete sign-in there.</p>}
      {!unconfirmed && <>
        <label className="block">Provider operation
          <select value={authenticated ? 'link' : intent} onChange={event => setIntent(event.target.value)} className="block n-panel p-2 mt-2" disabled={loading}>
            {!authenticated && <><option value="login">Log in</option><option value="signup">Create account</option></>}
            {authenticated && <option value="link">Explicitly link another provider</option>}
          </select>
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">{['google', 'github'].map(provider => <button key={provider}
          className="n-btn-ghost rounded-lg p-3 min-h-12 w-full focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 disabled:opacity-50" data-testid={`login-${provider}-btn`}
          disabled={loading || !auth.providers[provider]} onClick={() => run(async () => {
            setRedirecting(true);
            try { await auth.startOAuth(provider, authenticated ? 'link' : intent); }
            catch (failure) { setRedirecting(false); throw failure; }
          })}>
          {authenticated ? 'Connect' : 'Continue with'} {provider === 'google' ? 'Google' : 'GitHub'}{!auth.providers[provider] ? ' — not configured' : ''}
        </button>)}</div>
      </>}
      {(authenticated || unconfirmed) && <button className="n-btn-ghost rounded-lg p-3" disabled={loading}
        data-testid="logout-btn" onClick={() => run(auth.logout)}>{unconfirmed ? 'Retry server sign-out' : 'Sign out'}</button>}
      <button className="n-btn-ghost rounded-lg p-3" disabled={loading || unconfirmed} onClick={() => run(auth.refresh)}>Recheck server session</button>
    </section>
  </main>;
}
