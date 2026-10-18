import React, { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Settings, LogOut, User, ChevronDown, Shield, Palette, Bot, Moon, Volume2 } from 'lucide-react';
import { useUserPrefs } from '../state/UserPrefsContext';
import { useConversation } from '../state/ConversationContext';
import { useVoice } from '../state/VoiceContext';
import { useAuth } from '../state/AuthContext';
import Avatar from './Avatar';
import { mode } from '../services/api';

export default function ProfileDropdown() {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  const nav = useNavigate();
  const { prefs, gradientClass } = useUserPrefs();
  const { reset } = useConversation();
  const { mic, setDraft } = useVoice();
  const { logout, identity } = useAuth();
  const live = mode !== 'demo';
  const profile = live ? { displayName: identity?.actor || 'Session unavailable', role: identity?.role || 'Unknown role', org: 'Authenticated API identity', initials: (identity?.actor || '?').slice(0, 2).toUpperCase() } : prefs;
  const [signingOut, setSigningOut] = useState(false);
  const [logoutError, setLogoutError] = useState(null);

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  // Close on Escape
  useEffect(() => {
    if (!open) return;
    const handler = (e) => { if (e.key === 'Escape') setOpen(false); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [open]);

  const handleSignOut = async () => {
    setSigningOut(true);
    setLogoutError(null);
    mic.stop();
    setDraft('');
    reset();
    try {
      if (!await logout()) {
        setLogoutError('Server sign-out is unconfirmed. Retry before leaving this browser.');
        return;
      }
      setOpen(false);
      nav('/login');
    } catch {
      setLogoutError('Server sign-out could not be confirmed. Retry before leaving this browser.');
    } finally {
      setSigningOut(false);
    }
  };

  return (
    <div ref={ref} className="relative" data-testid="profile-dropdown-container">
      {/* Trigger */}
      <button
        onClick={() => setOpen(v => !v)}
        className="flex items-center gap-2 pl-3 border-l border-[color:var(--n-stroke-soft)] hover:bg-white/5 rounded-lg py-1 pr-2 transition-colors group"
        data-testid="profile-dropdown-trigger"
        aria-expanded={open}
        aria-haspopup="true"
      >
        <Avatar
          size="sm"
          initials={profile.initials}
          gradient={`bg-gradient-to-br ${gradientClass}`}
          className="group-hover:scale-105"
        />
        <div className="text-xs leading-tight hidden xl:block text-left">
          <div className="text-[color:var(--n-text)] font-medium">{profile.displayName}</div>
          <div className="text-[color:var(--n-text-subtle)]">{profile.org}</div>
        </div>
        <ChevronDown
          size={12}
          className={`text-[color:var(--n-text-mute)] transition-transform duration-200 hidden xl:block ${open ? 'rotate-180' : ''}`}
        />
      </button>

      {/* Dropdown Panel */}
      {open && (
        <div
          className="absolute right-0 top-full mt-2 w-72 rounded-2xl border border-[color:var(--n-stroke-soft)] n-glass shadow-[0_20px_60px_-15px_rgba(0,0,0,0.7)] overflow-hidden z-50 animate-in fade-in slide-in-from-top-2 duration-200"
          data-testid="profile-dropdown-panel"
        >
          {logoutError && <p role="alert" className="px-4 pt-3 text-xs text-red-400">{logoutError}</p>}
          {/* User Info Header */}
          <div className="px-4 py-4 border-b border-[color:var(--n-stroke-soft)] bg-gradient-to-r from-[rgba(46,155,255,0.08)] to-[rgba(196,30,42,0.06)]">
            <div className="flex items-center gap-3">
              <Avatar
                size="lg"
                initials={profile.initials}
                gradient={`bg-gradient-to-br ${gradientClass}`}
              />
              <div className="flex-1 min-w-0">
                <div className="text-sm font-semibold text-[color:var(--n-text)] truncate">{profile.displayName}</div>
                <div className="text-[11px] text-[color:var(--n-text-mute)] truncate">{profile.role}</div>
                <div className="text-[10px] text-[color:var(--n-text-subtle)] truncate mt-0.5">{profile.org}</div>
              </div>
            </div>

            {/* Quick Status Chips */}
            <div className="flex items-center gap-1.5 mt-3">
              <span className="n-chip-green n-chip text-[9px]">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse inline-block mr-1" />
                {live ? 'Signed in' : 'Online'}
              </span>
              {!live && <span className="n-chip text-[9px] bg-[rgba(46,155,255,0.12)] text-[#2E9BFF] border border-[rgba(46,155,255,0.25)]">
                <Bot size={9} className="mr-1 inline" />
                AI Active
              </span>}
            </div>
          </div>

          {/* Quick Settings */}
          {!live && <div className="px-2 py-2 border-b border-[color:var(--n-stroke-soft)]">
            <div className="px-2 pt-1 pb-1.5 text-[9px] uppercase tracking-[0.15em] text-[color:var(--n-text-subtle)] font-medium">Quick Settings</div>
            
            <QuickToggle
              icon={Moon}
              label="Dark Theme"
              enabled={true}
              hint="Always on"
              locked
            />
            <QuickToggle
              icon={Volume2}
              label="Voice Composer"
              enabled={prefs.ai.voiceEnabled}
              hint={prefs.ai.voiceEnabled ? 'Enabled' : 'Disabled'}
            />
            <QuickToggle
              icon={Bot}
              label="Auto-Citation"
              enabled={prefs.ai.autoCitation}
              hint={prefs.ai.autoCitation ? 'On' : 'Off'}
            />
          </div>}

          {/* Navigation Links */}
          <div className="px-2 py-2">
            <DropdownLink
              icon={User}
              label="Profile & Account"
              to={live ? "/login" : "/app/settings"}
              onClick={() => setOpen(false)}
            />
            <DropdownLink
              icon={Settings}
              label="Settings"
              to="/app/settings"
              onClick={() => setOpen(false)}
            />
            <DropdownLink
              icon={Shield}
              label="Governance & Audit"
              to="/app/governance"
              onClick={() => setOpen(false)}
            />
            {!live && <DropdownLink
              icon={Palette}
              label="Demo Controls"
              to="/app/demo-controls"
              onClick={() => setOpen(false)}
            />}
          </div>

          {/* Sign Out */}
          <div className="px-2 py-2 border-t border-[color:var(--n-stroke-soft)]">
            <button
              onClick={handleSignOut}
              disabled={signingOut}
              className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs text-[#F24F61] hover:bg-[rgba(242,79,97,0.1)] transition-colors"
              data-testid="profile-signout-btn"
            >
              <LogOut size={14} />
              <span>{signingOut ? 'Signing Out…' : 'Sign Out'}</span>
              <span className="ml-auto text-[10px] text-[color:var(--n-text-subtle)]">Clears local state</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function QuickToggle({ icon: Icon, label, enabled, hint, locked = false }) {
  return (
    <div className="flex items-center gap-2.5 px-3 py-1.5 rounded-lg text-xs hover:bg-white/5 transition-colors">
      <Icon size={13} className="text-[color:var(--n-text-mute)] shrink-0" />
      <span className="flex-1 text-[color:var(--n-text)]">{label}</span>
      <span className="text-[10px] text-[color:var(--n-text-subtle)]">{hint}</span>
      <div className={`w-7 h-4 rounded-full relative transition-colors ${
        locked ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
      } ${enabled ? 'bg-[#2E9BFF]' : 'bg-[color:var(--n-stroke-strong)]'}`}>
        <span className={`absolute top-0.5 left-0.5 w-3 h-3 rounded-full bg-white transition-transform ${enabled ? 'translate-x-3' : 'translate-x-0'}`} />
      </div>
    </div>
  );
}

function DropdownLink({ icon: Icon, label, to, onClick }) {
  return (
    <Link
      to={to}
      onClick={onClick}
      className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs text-[color:var(--n-text-mute)] hover:bg-white/5 hover:text-[color:var(--n-text)] transition-colors"
    >
      <Icon size={14} className="shrink-0" />
      <span>{label}</span>
    </Link>
  );
}
