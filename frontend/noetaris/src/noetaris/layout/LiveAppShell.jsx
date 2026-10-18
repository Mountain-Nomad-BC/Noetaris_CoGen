import React from 'react';
import { Link, NavLink, Outlet } from 'react-router-dom';
import Logo from '../brand/Logo';
import { useAuth } from '../state/AuthContext';

export default function LiveAppShell() {
  const auth = useAuth();
  return <div className="min-h-screen" data-testid="live-app-shell">
    <header className="n-glass p-4 flex flex-wrap items-center gap-4 border-b border-[color:var(--n-stroke-soft)]">
      <Link to="/"><Logo /></Link>
      <NavLink to="/app/library" className="n-btn-ghost rounded-lg p-2">Document library</NavLink>
      <NavLink to="/app/knowledge" className="n-btn-ghost rounded-lg p-2">Knowledge Atlas</NavLink>
      {auth.identity.permissions?.includes('chat')&&<NavLink to="/app/memory" className="n-btn-ghost rounded-lg p-2">Memory</NavLink>}
      {auth.identity.permissions?.some(value=>['propose','review'].includes(value))&&<NavLink to="/app/learning" className="n-btn-ghost rounded-lg p-2">Reflection proposals</NavLink>}
      {auth.identity.permissions?.includes('review')&&<NavLink to="/app/knowledge/review" className="n-btn-ghost rounded-lg p-2">Source claim review</NavLink>}
      <NavLink to="/app/approvals" className="n-btn-ghost rounded-lg p-2">Governed candidates</NavLink>
      <NavLink to="/app/chat" className="n-btn-ghost rounded-lg p-2">Conversations</NavLink>
      {auth.identity.permissions?.includes('admin')&&<NavLink to="/app/costs" className="n-btn-ghost rounded-lg p-2">Usage governance</NavLink>}
      <Link to="/login" className="n-btn-ghost rounded-lg p-2">Account</Link>
      <span className="n-chip">LIVE BACKEND</span>
      <span className="text-xs break-all" data-testid="live-identity">{auth.identity.actor} · {auth.identity.role}</span>
      <button className="n-btn-ghost rounded-lg p-2" onClick={auth.logout} data-testid="topbar-signout-btn">Sign out</button>
    </header>
    <main><Outlet /></main>
  </div>;
}
