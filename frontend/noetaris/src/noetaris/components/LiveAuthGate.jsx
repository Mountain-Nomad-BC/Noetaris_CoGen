import React from 'react';
import { mode } from '../services/api';
import { useAuth } from '../state/AuthContext';
import { useLocation } from 'react-router-dom';

// Backend content admission and read permission are required independently of login.
export default function LiveAuthGate({ children }) {
  const auth = useAuth();
  const { pathname } = useLocation();

  if (mode === 'demo') return children;

  if (auth.status === 'authenticated' && 
      auth.capabilities?.content_access?.admitted === true &&
      auth.identity.permissions?.includes('read')) {
    return children;
  }

  return (
    <main role="alert" className="min-h-screen flex items-center justify-center p-8" data-testid="live-auth-gate">
      <section className="n-glass rounded-2xl p-8 max-w-xl">
        <p className="n-chip n-chip-amber inline-block mb-4">AUTHENTICATION REQUIRED</p>
        <h1 className="font-display text-2xl mb-3">Workspace Access Control</h1>
        <p role="status" className="text-sm mb-3 text-[color:var(--n-text-mute)]">
          {auth.status === 'authenticated' 
            ? `Server identity: ${auth.identity.actor}.` 
            : auth.status === 'loading' 
            ? 'Checking the canonical server session…' 
            : 'Sign in with a server-verified identity to access the Noetaris engineering workspace.'}
        </p>
        {auth.status === 'authenticated' && (
          <p className="text-xs text-[color:var(--n-text-subtle)] mb-4">
            {auth.capabilities?.content_access?.reason || 'Verified identity connected. Loading workspace telemetry…'}
          </p>
        )}
        {auth.error && <p role="alert" className="text-xs text-red-400 mb-4">{auth.error}</p>}
        <a href="/login" className="n-cta inline-flex px-5 py-2 mt-3 text-xs">
          Proceed to Sign-In
        </a>
      </section>
    </main>
  );
}
